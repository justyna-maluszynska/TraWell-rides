import datetime

from django.db.models import QuerySet
from django.http import JsonResponse
from rest_framework import viewsets, status
from rest_framework.decorators import action

from rides import tasks
from rides.filters import RideFilter
from rides.models import Ride, Participation
from rides.serializers import RideSerializer, RideListSerializer, RidePersonal, ParticipationNestedSerializer
from django_filters import rest_framework as filters
from rest_framework.filters import OrderingFilter

from rides.utils.utils import find_city_object, find_near_cities, get_city_info, verify_request, get_user_vehicle, \
    filter_input_data, get_duration
from users.models import User
from rides.utils.CustomPagination import CustomPagination
from rides.utils.validate_token import validate_token
from users.serializers import UserSerializer


class RideViewSet(viewsets.ModelViewSet):
    """
    API View Set that allows Rides to be viewed, created, updated or deleted.
    This viewset automatically provides list and detail actions.
    """

    serializer_classes = {
        'get_filtered': RideListSerializer,
        'retrieve': RideSerializer,
        'user_rides': RidePersonal,
        'create': RideSerializer,
    }
    queryset = Ride.objects.filter(is_cancelled=False, start_date__gt=datetime.datetime.today())
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
        :return: queryset with all available rides from city_from + nearest cities to city_to
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

    def _validate_values(self, vehicle, duration, serializer, user) -> (bool, str):
        if vehicle is None and user.private:
            return False, 'Vehicle parameter is invalid'
        if duration is None:
            return False, 'Duration parameter is invalid'
        if not serializer.is_valid():
            return False, serializer.errors
        return True, 'OK'

    def _create_new_ride(self, request, user):
        data = request.data
        cleared_data = filter_input_data(data, expected_keys=['city_from', 'city_to', 'area_from', 'area_to',
                                                              'start_date', 'price', 'seats', 'vehicle',
                                                              'duration', 'description', 'coordinates',
                                                              'automatic_confirm'])

        vehicle = get_user_vehicle(data=cleared_data, user=user)
        duration = get_duration(cleared_data)

        if user.private:
            cleared_data['automatic_confirm'] = False

        serializer = self.get_serializer_class()(data=cleared_data,
                                                 context={'driver': user, 'vehicle': vehicle, 'duration': duration})

        is_valid, message = self._validate_values(vehicle=vehicle, duration=duration, serializer=serializer, user=user)
        if is_valid:
            serializer.save()

            tasks.publish_message(serializer.data)

            return JsonResponse(status=status.HTTP_200_OK, data=serializer.data, safe=False)
        else:
            return JsonResponse(status=status.HTTP_400_BAD_REQUEST, data=message, safe=False)

    @validate_token
    def create(self, request, *args, **kwargs):
        token = kwargs['decoded_token']
        user_email = token['email']

        print('creating ride')
        print(request.data)

        print('Try to publish with celery')
        # tasks.publish_message({'hello': 'world'})
        # print('published')

        try:
            user = User.objects.get(email=user_email)
        except User.DoesNotExist:
            return JsonResponse(status=status.HTTP_404_NOT_FOUND, data="User not found", safe=False)

        response = self._create_new_ride(request=request, user=user)
        return response

    def _verify_available_seats(self, data):
        instance = self.get_object()

        if data['seats'] < instance.seats - instance.available_seats:
            return False
        return True

    def _update_serializer(self, data, context) -> JsonResponse:
        instance = self.get_object()
        serializer = self.get_serializer(instance=instance, data=data, partial=True)
        if serializer.is_valid():
            tasks.publish_message(serializer.data)

            serializer.update(instance=instance, validated_data=data, partial=True, context=context)
            return JsonResponse(status=status.HTTP_200_OK, data=serializer.data, safe=False)

        return JsonResponse(status=status.HTTP_400_BAD_REQUEST, data=serializer.errors, safe=False)

    def _update_partial_ride(self, update_data, user):
        context = {}

        if user.private:
            expected_keys = ['seats', 'vehicle', 'description']
            vehicle = get_user_vehicle(update_data, user)
            context['vehicle'] = vehicle
        else:
            expected_keys = ['seats', 'automatic_confirm', 'description']

        cleared_data = filter_input_data(update_data, expected_keys=expected_keys)
        if self._verify_available_seats(data=cleared_data):
            return JsonResponse(status=status.HTTP_405_METHOD_NOT_ALLOWED, data="Invalid seats parameter",
                                safe=False)

        return self._update_serializer(data=cleared_data, context=context)

    def _update_whole_ride(self, update_data, user) -> JsonResponse:
        cleared_data = filter_input_data(update_data,
                                         expected_keys=['city_from', 'city_to', 'area_from', 'area_to',
                                                        'start_date', 'price', 'seats', 'vehicle',
                                                        'duration', 'description', 'coordinates',
                                                        'automatic_confirm'])

        context = {}
        vehicle = get_user_vehicle(data=cleared_data, user=user)
        if user.private:
            context['vehicle'] = vehicle

        duration = get_duration(cleared_data)
        if duration is not None:
            context['duration'] = duration

        if user.private:
            cleared_data['automatic_confirm'] = False

        return self._update_serializer(data=cleared_data, context=context)

    def _is_user_a_driver(self, user) -> bool:
        return self.get_object().driver == user

    def _has_ride_passengers(self) -> bool:
        return self.get_object().passengers.filter(
            passenger__decision__in=[Participation.Decision.ACCEPTED, Participation.Decision.PENDING]).exists()

    def _update_ride(self, request, user) -> JsonResponse:
        if self._is_user_a_driver(user):
            if request.method == 'PATCH':
                update_data = request.data
                if self._has_ride_passengers():
                    return self._update_partial_ride(update_data, user)
                else:
                    return self._update_whole_ride(update_data, user)
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
        token = kwargs['decoded_token']
        user_email = token['email']

        try:
            user = User.objects.get(email=user_email)
        except User.DoesNotExist:
            return JsonResponse(status=status.HTTP_404_NOT_FOUND, data="User not found", safe=False)

        return self._update_ride(request=request, user=user)

    @validate_token
    def destroy(self, request, *args, **kwargs):
        token = kwargs['decoded_token']
        user_email = token['email']

        try:
            user = User.objects.get(email=user_email)
        except User.DoesNotExist:
            return JsonResponse(status=status.HTTP_404_NOT_FOUND, data="User not found", safe=False)

        instance = self.get_object()
        if instance.driver == user:
            instance.is_cancelled = True
            instance.save()

            tasks.publish_message(UserSerializer.data)

            return JsonResponse(status=status.HTTP_200_OK, data=f'Ride successfully deleted.', safe=False)
        else:
            return JsonResponse(status=status.HTTP_405_METHOD_NOT_ALLOWED, data="User not allowed to delete ride",
                                safe=False)

    @validate_token
    @action(detail=False, methods=['get'])
    def user_rides(self, request, *args, **kwargs):
        """
        Endpoint for getting user rides. Can be filtered with price (from - to), from place, to place
        :param request:
        :return: List of user's rides.
        """
        token = kwargs['decoded_token']
        user_email = token['email']

        try:
            user = User.objects.get(email=user_email)
        except User.DoesNotExist:
            return JsonResponse(status=status.HTTP_404_NOT_FOUND, data="User not found", safe=False)

        queryset = self.get_queryset()
        try:
            user_ride_type = request.GET['user_type']

            if user_ride_type == 'driver':
                rides = queryset.filter(driver=user)
            elif user_ride_type == 'passenger':
                rides = queryset.filter(passengers=user, participation__decision=Participation.Decision.ACCEPTED)
            else:
                return JsonResponse(status=status.HTTP_400_BAD_REQUEST, data="Invalid user_type parameter", safe=False)
        except KeyError as e:
            return JsonResponse(status=status.HTTP_400_BAD_REQUEST, data=f"Missing parameter {e}", safe=False)
        try:
            city_from_dict = get_city_info(request.GET, 'from')
            rides = rides.filter(city_from__name=city_from_dict['name'], city_from__state=city_from_dict['state'],
                                 city_from__county=city_from_dict['county'])
        except KeyError:
            pass

        try:
            city_to_dict = get_city_info(request.GET, 'to')
            rides = rides.filter(city_to__name=city_to_dict['name'],
                                 city_to__state=city_to_dict['state'],
                                 city_to__county=city_to_dict['county'])
        except KeyError:
            pass

        filtered_rides = self.filter_queryset(rides)
        return self._get_paginated_queryset(filtered_rides)

    @validate_token
    @action(detail=True, methods=['post'])
    def send_request(self, request, pk=None, *args, **kwargs):
        """
        Endpoint for sending request to join a ride.
        :param request:
        :param pk:
        :return:
        """
        token = kwargs['decoded_token']
        user_email = token['email']

        try:
            user = User.objects.get(email=user_email)
        except User.DoesNotExist:
            return JsonResponse(status=status.HTTP_404_NOT_FOUND, data="User not found", safe=False)

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

            tasks.publish_message(participation.data)

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
        token = kwargs['decoded_token']
        user_email = token['email']

        try:
            user = User.objects.get(email=user_email)
        except User.DoesNotExist:
            return JsonResponse(status=status.HTTP_404_NOT_FOUND, data="User not found", safe=False)

        try:
            participation = Participation.objects.get(id=request_id)
        except Participation.DoesNotExist:
            return JsonResponse(status=status.HTTP_404_NOT_FOUND, data="Request not found", safe=False)

        if participation.ride.driver == user:
            data = request.data
            try:
                requesting_user = User.objects.get(user_id=data['driver_id'])
                if participation.ride.driver == requesting_user and participation.decision == participation.Decision.PENDING:
                    decision = data['decision']
                    if decision in [choice[0] for choice in Participation.Decision.choices]:
                        participation.decision = decision
                        participation.save()

                        tasks.publish_message(ParticipationNestedSerializer.data)

                        return JsonResponse(status=status.HTTP_200_OK,
                                            data=f'Request successfully changed to {decision}',
                                            safe=False)
                    else:
                        return JsonResponse(status=status.HTTP_400_BAD_REQUEST,
                                            data=f"Invalid decision parameter value",
                                            safe=False)
                return JsonResponse(status=status.HTTP_405_METHOD_NOT_ALLOWED,
                                    data=f"Request do not have {participation.Decision.PENDING} status", safe=False)
            except User.DoesNotExist:
                return JsonResponse(status=status.HTTP_404_NOT_FOUND, data="User not found", safe=False)
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
        token = kwargs['decoded_token']
        user_email = token['email']

        try:
            user = User.objects.get(email=user_email)
        except User.DoesNotExist:
            return JsonResponse(status=status.HTTP_404_NOT_FOUND, data="User not found", safe=False)

        try:
            participation = Participation.objects.get(id=request_id)
        except Participation.DoesNotExist:
            return JsonResponse(status=status.HTTP_404_NOT_FOUND, data="Request not found", safe=False)

        if participation.user == user:
            try:
                if participation.decision != Participation.Decision.CANCELLED:
                    participation.decision = Participation.Decision.CANCELLED
                    participation.save()

                    tasks.publish_message(ParticipationNestedSerializer.data)

                    return JsonResponse(status=status.HTTP_200_OK, data=f'Request successfully cancelled ', safe=False)
                else:
                    return JsonResponse(status=status.HTTP_405_METHOD_NOT_ALLOWED, data=f"Request is already cancelled",
                                        safe=False)
            except KeyError as e:
                return JsonResponse(status=status.HTTP_400_BAD_REQUEST, data=f"Missing parameter: {e}", safe=False)
        else:
            return JsonResponse(status=status.HTTP_405_METHOD_NOT_ALLOWED,
                                data="User not allowed to delete request", safe=False)

    @validate_token
    @action(detail=True, methods=['get'])
    def check_edition_permissions(self, request, pk=None, *args, **kwargs):
        token = kwargs['decoded_token']
        user_email = token['email']

        try:
            user = User.objects.get(email=user_email)
        except User.DoesNotExist:
            return JsonResponse(status=status.HTTP_404_NOT_FOUND, data="User not found", safe=False)

        instance = self.get_object()
        if instance.driver == user:
            full_permission = not self._has_ride_passengers()
            return JsonResponse(status=status.HTTP_200_OK, data={'full_permission': full_permission}, safe=False)
        else:
            return JsonResponse(status=status.HTTP_405_METHOD_NOT_ALLOWED, data="User not allowed to update a ride",
                                safe=False)
