from django.db.models import QuerySet
from django.http import JsonResponse
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter

from django_filters import rest_framework as filters

from recurrent_rides.filters import RecurrentRideFilter
from recurrent_rides.models import RecurrentRide
from recurrent_rides.serializers import RecurrentRideSerializer, RecurrentRidePersonal
from rides.models import Ride
from utils.CustomPagination import CustomPagination
from rides.utils.constants import ACTUAL_RIDES_ARGS
from utils.services import create_new_ride, update_partial_ride, cancel_ride
from utils.utils import is_user_a_driver, filter_rides_by_cities
from utils.validate_token import validate_token


# Create your views here.
class RecurrentRideViewSet(viewsets.ModelViewSet):
    serializer_classes = {
        'create': RecurrentRideSerializer,
        'update': RecurrentRideSerializer,
        'user_rides': RecurrentRidePersonal,
        'retrieve': RecurrentRideSerializer,
    }
    queryset = RecurrentRide.objects.filter(**ACTUAL_RIDES_ARGS)
    filter_backends = [filters.DjangoFilterBackend, OrderingFilter]
    filterset_class = RecurrentRideFilter
    pagination_class = CustomPagination
    ordering_fields = ['price', 'start_date', 'duration']

    def get_serializer_class(self):
        return self.serializer_classes.get(self.action) or RecurrentRideSerializer

    def get_paginated_queryset(self, queryset: QuerySet) -> JsonResponse:
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(page, many=True)
        return JsonResponse(status=status.HTTP_200_OK, data=serializer.data, safe=False)

    def _create_new_recurrent_ride(self, request, user):
        data = request.data
        expected_keys = ['city_from', 'city_to', 'area_from', 'area_to', 'start_date', 'price', 'seats', 'vehicle',
                         'duration', 'description', 'coordinates', 'automatic_confirm', 'frequency_type', 'frequence',
                         'occurrences', 'end_date']

        status_code, message = create_new_ride(data=data, keys=expected_keys, user=user,
                                               serializer=self.get_serializer_class())

        return JsonResponse(status=status_code, data=message, safe=False)

    @validate_token
    def create(self, request, *args, **kwargs):
        user = kwargs['user']

        response = self._create_new_recurrent_ride(request=request, user=user)
        return response

    def _update_recurrent_ride(self, request, user) -> JsonResponse:
        if is_user_a_driver(user, self.get_object()):
            if request.method == 'PATCH':
                args = {
                    "instance": self.get_object(),
                    "serializer": self.get_serializer_class(),
                    "update_data": request.data,
                    "user": user
                }
                status_code, message = update_partial_ride(**args)
                return JsonResponse(status=status_code, data=message, safe=False)
        else:
            return JsonResponse(status=status.HTTP_405_METHOD_NOT_ALLOWED, data="User not allowed to update a ride",
                                safe=False)

    @validate_token
    def update(self, request, *args, **kwargs):
        user = kwargs['user']

        return self._update_recurrent_ride(request=request, user=user)

    @validate_token
    def destroy(self, request, *args, **kwargs):
        user = kwargs['user']

        instance = self.get_object()
        if instance.driver == user:
            cancel_ride(instance)
            singular_rides = Ride.objects.filter(recurrent_ride=instance, **ACTUAL_RIDES_ARGS)
            for ride in singular_rides:
                cancel_ride(ride)
            return JsonResponse(status=status.HTTP_200_OK, data=f'Ride successfully deleted.', safe=False)
        else:
            return JsonResponse(status=status.HTTP_405_METHOD_NOT_ALLOWED, data="User not allowed to delete ride",
                                safe=False)

    def _get_user_rides(self, request, user):
        queryset = self.get_queryset()
        rides = queryset.filter(driver=user)

        rides = filter_rides_by_cities(request, rides)
        filtered_rides = self.filter_queryset(rides)
        return self.get_paginated_queryset(filtered_rides)

    @validate_token
    @action(detail=False, methods=['get'])
    def user_rides(self, request, *args, **kwargs):
        """
        Endpoint for getting user recurrent rides. Can be filtered with price (from - to), from place, to place
        :param request:
        :return: List of user's recurrent rides.
        """
        user = kwargs['user']

        return self._get_user_rides(request, user)
