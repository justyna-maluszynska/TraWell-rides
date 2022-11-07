from django.db.models import QuerySet
from django.http import JsonResponse
from rest_framework import viewsets, status
from rest_framework.decorators import action

from rides import tasks
from rides.filters import RideFilter, RecurrentRideFilter
from rides.models import Ride, Participation, RecurrentRide
from rides.serializers import RideSerializer, RideListSerializer, RidePersonal, ParticipationSerializer, \
    RecurrentRideSerializer, RecurrentRidePersonal, ParticipationAllSerializer
from django_filters import rest_framework as filters
from rest_framework.filters import OrderingFilter

from rides.services import create_new_ride, update_partial_ride, update_whole_ride, cancel_ride
from rides.utils.constants import ACTUAL_RIDES_ARGS
from rides.utils.utils import find_city_object, find_near_cities, get_city_info, verify_request, filter_by_decision, \
    filter_rides_by_cities, is_user_a_driver
from rides.utils.CustomPagination import CustomPagination
from rides.utils.validate_token import validate_token


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
        'my_requests': ParticipationSerializer,
        'pending_requests': ParticipationSerializer,
    }
    queryset = Ride.objects.filter(**ACTUAL_RIDES_ARGS)
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
        city_to_obj = find_city_object(city_to)

        if city_to_obj is not None:
            queryset = self.get_queryset()
            queryset = queryset.filter(city_to__name=city_to_obj.name, city_to__state=city_to_obj.state,
                                       city_to__county=city_to_obj.county,
                                       available_seats__gt=0)

            if not queryset.exists():
                # There are no rides to given city destination, no sense to check the rest of parameters
                return queryset

            near_cities_ids = find_near_cities(city_from)

            queryset_with_near_cities = queryset.filter(city_from__city_id__in=near_cities_ids)
            filtered_queryset = self.filter_queryset(queryset_with_near_cities)
            return filtered_queryset
        else:
            return Ride.objects.none()

    def _get_paginated_queryset(self, queryset: QuerySet) -> JsonResponse:
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(page, many=True)
        return JsonResponse(status=status.HTTP_200_OK, data=serializer.data, safe=False)

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

        return self._get_paginated_queryset(filtered_queryset)

    def _create_new_ride(self, request, user):
        data = request.data
        expected_keys = ['city_from', 'city_to', 'area_from', 'area_to', 'start_date', 'price', 'seats', 'vehicle',
                         'duration', 'description', 'coordinates', 'automatic_confirm']

        status_code, message = create_new_ride(data=data, keys=expected_keys, user=user,
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
        return self._get_paginated_queryset(filtered_rides)

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

    # REQUESTS ENDPOINTS

    @validate_token
    @action(detail=True, methods=['post'])
    def send_request(self, request, pk=None, *args, **kwargs):
        """
        Endpoint for sending request to join a ride.
        :param request:
        :param pk:
        :return:
        """
        user = kwargs['user']

        parameters = request.data
        try:
            seats_no = parameters['seats']
        except KeyError as e:
            return JsonResponse(status=status.HTTP_400_BAD_REQUEST, data=f"Missing parameter: {e}", safe=False)

        instance = self.get_object()

        is_correct, message = verify_request(user=user, ride=instance, seats=seats_no)

        if is_correct:
            decision = Participation.Decision.ACCEPTED if instance.automatic_confirm else Participation.Decision.PENDING
            participation = Participation.objects.create(ride=instance, user=user, decision=decision, reserved_seats=seats_no)
            tasks.publish_message(ParticipationAllSerializer(participation).data, 'participation')

            return JsonResponse(status=status.HTTP_200_OK, data='Request successfully sent', safe=False)
        else:
            return JsonResponse(status=status.HTTP_400_BAD_REQUEST, data=message, safe=False)

    @validate_token
    @action(detail=False, methods=['post'], url_path=r'request/(?P<request_id>[^/.]+)', )
    def request(self, request, request_id, *args, **kwargs):
        """
        Endpoint for drivers to accept or decline pending requests.
        :param request:
        :param request_id:
        :return:
        """
        user = kwargs['user']

        try:
            participation = Participation.objects.get(id=request_id)
        except Participation.DoesNotExist:
            return JsonResponse(status=status.HTTP_404_NOT_FOUND, data="Request not found", safe=False)

        if participation.ride.driver == user:
            data = request.data
            try:
                if participation.decision == participation.Decision.PENDING:
                    decision = data['decision']
                    if decision in [choice[0] for choice in Participation.Decision.choices]:
                        participation.decision = decision
                        participation.save()
                        tasks.publish_message(ParticipationAllSerializer(participation).data, 'participation')

                        return JsonResponse(status=status.HTTP_200_OK,
                                            data=f'Request successfully changed to {decision}', safe=False)
                    else:
                        return JsonResponse(status=status.HTTP_400_BAD_REQUEST,
                                            data=f"Invalid decision parameter value", safe=False)
                return JsonResponse(status=status.HTTP_405_METHOD_NOT_ALLOWED,
                                    data=f"Request do not have {participation.Decision.PENDING} status", safe=False)
            except KeyError as e:
                return JsonResponse(status=status.HTTP_400_BAD_REQUEST, data=f"Missing parameter: {e}", safe=False)
        else:
            return JsonResponse(status=status.HTTP_405_METHOD_NOT_ALLOWED, data="User not allowed to delete request",
                                safe=False)

    @validate_token
    @request.mapping.delete
    def delete_request(self, request, request_id, *args, **kwargs):
        """
        Endpoint for removing sent requests
        :param request:
        :param request_id:
        :return:
        """
        user = kwargs['user']

        try:
            participation = Participation.objects.get(id=request_id)
        except Participation.DoesNotExist:
            return JsonResponse(status=status.HTTP_404_NOT_FOUND, data="Request not found", safe=False)

        if participation.user == user:
            if participation.decision != Participation.Decision.CANCELLED:
                participation.decision = Participation.Decision.CANCELLED
                participation.save()
                tasks.publish_message(ParticipationAllSerializer(participation).data, 'participation')

                return JsonResponse(status=status.HTTP_200_OK, data=f'Request successfully cancelled ', safe=False)

            return JsonResponse(status=status.HTTP_405_METHOD_NOT_ALLOWED, data=f"Request is already cancelled",
                                safe=False)

        return JsonResponse(status=status.HTTP_405_METHOD_NOT_ALLOWED, data="User not allowed to delete request",
                            safe=False)

    @validate_token
    @action(detail=True, methods=['get'])
    def check_edition_permissions(self, request, pk=None, *args, **kwargs):
        user = kwargs['user']

        instance = self.get_object()
        if instance.driver == user:
            full_permission = not self._has_ride_passengers()
            return JsonResponse(status=status.HTTP_200_OK, data={'full_permission': full_permission}, safe=False)
        else:
            return JsonResponse(status=status.HTTP_405_METHOD_NOT_ALLOWED, data="User not allowed to update a ride",
                                safe=False)

    @validate_token
    @action(detail=False, methods=['get'])
    def my_requests(self, request, *args, **kwargs):
        user = kwargs['user']

        rides = self.get_queryset().filter(passengers=user)
        rides = filter_rides_by_cities(request, queryset=rides)

        filtered_rides = self.filter_queryset(rides)

        rides_ids = [ride.ride_id for ride in filtered_rides]

        decision = request.GET.get('decision', '')
        requests = filter_by_decision(decision, rides_ids, user)

        return self._get_paginated_queryset(requests)

    @validate_token
    @action(detail=False, methods=['get'])
    def pending_requests(self, request, *args, **kwargs):
        user = kwargs['user']

        rides = self.get_queryset().filter(driver=user)
        rides = filter_rides_by_cities(request, queryset=rides)

        filtered_rides = self.filter_queryset(rides)

        rides_ids = [ride.ride_id for ride in filtered_rides]

        requests = Participation.objects.filter(ride__ride_id__in=rides_ids, ride__driver=user,
                                                decision=Participation.Decision.PENDING)

        return self._get_paginated_queryset(requests)
