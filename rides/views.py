import datetime

from django.db.models import QuerySet
from django.http import JsonResponse
from rest_framework import viewsets, status
from rest_framework.decorators import action

from rides.filters import RideFilter
from rides.models import Ride, Participation
from rides.serializers import RideSerializer, RideListSerializer, RidePersonal
from django_filters import rest_framework as filters
from rest_framework.filters import OrderingFilter

from utils.generic_endpoints import get_paginated_queryset
from utils.selectors import city_object, rides_with_cities_nearby
from utils.services import create_or_update_ride, update_partial_ride, update_whole_ride, cancel_ride
from utils.utils import get_city_info, filter_rides_by_cities, is_user_a_driver
from utils.CustomPagination import CustomPagination
from utils.validate_token import validate_token


class RideViewSet(viewsets.ModelViewSet):
    """
    API View Set that allows Rides to be viewed, created, updated or deleted.
    This View Set automatically provides list and detail actions.
    """

    serializer_classes = {
        'get_filtered': RideListSerializer,
        'retrieve': RideSerializer,
        'user_rides': RidePersonal,
        'create': RideSerializer,
    }
    queryset = Ride.objects.filter(**{"is_cancelled": False, "start_date__gt": datetime.datetime.today()})
    filter_backends = [filters.DjangoFilterBackend, OrderingFilter]
    filterset_class = RideFilter
    pagination_class = CustomPagination
    ordering_fields = ['price', 'start_date', 'duration', 'available_seats']

    def get_serializer_class(self):
        return self.serializer_classes.get(self.action) or RideSerializer

    def _get_queryset_with_near_cities(self, city_from: dict, city_to: dict) -> QuerySet:
        """
        Gets queryset containing rides from cities near the starting city (city_from).
        The accepted range in km is defined in MAX_DISTANCE.

        :param city_from: dictionary with starting city data
        :param city_to: dictionary with destination city data
        :return: queryset with all available rides from city_from + the nearest cities to city_to
        """
        city_to_obj = city_object(city_to)

        if city_to_obj is not None:
            queryset = self.get_queryset()
            queryset_with_near_cities = rides_with_cities_nearby(queryset, city_to_obj, city_from)
            filtered_queryset = self.filter_queryset(queryset_with_near_cities)
            return filtered_queryset
        else:
            return Ride.objects.none()

    @action(detail=False, methods=['get'])
    def get_filtered(self, request, *args, **kwargs):
        """
        Endpoint for getting filtered rides.
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        parameters = request.GET
        try:
            city_from_dict = get_city_info(parameters, 'from')
            city_to_dict = get_city_info(parameters, 'to')
        except KeyError as e:
            return JsonResponse(status=status.HTTP_400_BAD_REQUEST, data=f"Missing parameter {e}", safe=False)

        try:
            filtered_queryset = self._get_queryset_with_near_cities(city_from_dict, city_to_dict)
        except ValueError as e:
            return JsonResponse(status=status.HTTP_400_BAD_REQUEST, data=f"Something went wrong: {e}", safe=False)

        return get_paginated_queryset(self, filtered_queryset)

    def _create_new_ride(self, request, user):
        data = request.data
        expected_keys = ['city_from', 'city_to', 'area_from', 'area_to', 'start_date', 'price', 'seats', 'vehicle',
                         'duration', 'description', 'coordinates', 'automatic_confirm']

        status_code, message = create_or_update_ride(data=data, keys=expected_keys, user=user,
                                                     serializer=self.get_serializer_class())

        return JsonResponse(status=status_code, data=message, safe=False)

    @validate_token
    def create(self, request, *args, **kwargs):
        user = kwargs['user']

        response = self._create_new_ride(request=request, user=user)
        return response

    def _has_ride_passengers(self) -> bool:
        return self.get_object().passengers.filter(
            passenger__decision__in=[Participation.Decision.ACCEPTED, Participation.Decision.PENDING]).exists()

    def _update_ride(self, request, user) -> JsonResponse:
        if is_user_a_driver(user, self.get_object()):
            if request.method == 'PATCH':
                args = {
                    "instance": self.get_object(),
                    "serializer": self.get_serializer_class(),
                    "update_data": request.data,
                    "user": user
                }
                if self._has_ride_passengers():
                    status_code, message = update_partial_ride(**args)
                else:
                    status_code, message = update_whole_ride(**args)
                return JsonResponse(status=status_code, data=message, safe=False)
        else:
            return JsonResponse(status=status.HTTP_405_METHOD_NOT_ALLOWED, data="User not allowed to update a ride",
                                safe=False)

    @validate_token
    def update(self, request, *args, **kwargs):
        """
        Endpoint for updating Ride object.
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        user = kwargs['user']

        return self._update_ride(request=request, user=user)

    @validate_token
    def destroy(self, request, *args, **kwargs):
        user = kwargs['user']

        instance = self.get_object()
        if instance.driver == user:
            cancel_ride(instance)
            return JsonResponse(status=status.HTTP_200_OK, data=f'Ride successfully deleted.', safe=False)
        else:
            return JsonResponse(status=status.HTTP_405_METHOD_NOT_ALLOWED, data="User not allowed to delete ride",
                                safe=False)

    def _get_user_rides(self, request, user):
        try:
            user_ride_type = request.GET['user_type']
            queryset = self.get_queryset()

            if user_ride_type == 'driver':
                rides = queryset.filter(driver=user)
            elif user_ride_type == 'passenger':
                rides = queryset.filter(passengers=user, participation__decision=Participation.Decision.ACCEPTED)
            else:
                return JsonResponse(status=status.HTTP_400_BAD_REQUEST, data="Invalid user_type parameter", safe=False)
        except KeyError as e:
            return JsonResponse(status=status.HTTP_400_BAD_REQUEST, data=f"Missing parameter {e}", safe=False)

        rides = filter_rides_by_cities(request, rides)
        filtered_rides = self.filter_queryset(rides)
        return get_paginated_queryset(self, filtered_rides)

    @validate_token
    @action(detail=False, methods=['get'])
    def user_rides(self, request, *args, **kwargs):
        """
        Endpoint for getting user rides. Can be filtered with price (from - to), from place, to place
        :param request:
        :return: List of user's rides.
        """
        user = kwargs['user']
        return self._get_user_rides(request, user)

    @validate_token
    @action(detail=True, methods=['get'])
    def check_edition_permissions(self, request, *args, **kwargs):
        user = kwargs['user']

        instance = self.get_object()
        if instance.driver == user:
            full_permission = not self._has_ride_passengers()
            return JsonResponse(status=status.HTTP_200_OK, data={'full_permission': full_permission}, safe=False)
        else:
            return JsonResponse(status=status.HTTP_405_METHOD_NOT_ALLOWED, data="User not allowed to update a ride",
                                safe=False)
