import datetime

from django.db.models import QuerySet
from django.http import JsonResponse
from rest_framework import viewsets, status
from rest_framework.decorators import action

from cities.models import City
from rides.filters import RideFilter
from rides.models import Ride, Participation, Coordinate
from rides.serializers import RideSerializer, RideListSerializer, RidePersonal
from django_filters import rest_framework as filters
from rest_framework.filters import OrderingFilter

from rides.utils import validate_hours_minutes, find_city_object, find_near_cities, get_city_info, verify_request
from users.models import User
from utils.CustomPagination import CustomPagination
from vehicles.models import Vehicle


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
    queryset = Ride.objects.filter(is_cancelled=False)
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
            queryset = queryset.filter(start_date__gt=datetime.datetime.today(), city_to__name=city_to_obj.name,
                                       city_to__state=city_to_obj.state, city_to__county=city_to_obj.county,
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

    def _update_ride_nested_fields(self, update_data: dict):
        instance = self.get_object()

        try:
            requested_city_from = update_data.pop('city_from')
            city_from, was_created = City.objects.get_or_create(**requested_city_from)
            instance.city_from = city_from
        except KeyError:
            pass

        try:
            requested_city_to = update_data.pop('city_to')
            city_to, was_created = City.objects.get_or_create(**requested_city_to)
            instance.city_to = city_to
        except KeyError:
            pass

        try:
            duration = update_data.pop('duration')
            hours = duration['hours']
            minutes = duration['minutes']
            if validate_hours_minutes(hours, minutes):
                instance.duration = datetime.timedelta(hours=hours, minutes=minutes)
            else:
                return JsonResponse(status=status.HTTP_400_BAD_REQUEST, data="Wrong duration parameter",
                                    safe=False)
        except KeyError:
            pass

        try:
            instance.coordinates.all().delete()
            coordinates = update_data.pop('coordinates')

            for coordinate in coordinates:
                Coordinate.objects.update_or_create(ride=instance, lat=coordinate['lat'], lng=coordinate['lng'],
                                                    defaults={'sequence_no': coordinate['sequence_no']})
        except KeyError:
            pass

        instance.save()
        return instance

    def _extract_ride_data(self, data: dict) -> (dict, dict, int, int, dict):
        return data.pop('city_from'), data.pop('city_to'), data.pop('driver'), data.pop('vehicle'), data.pop('duration')

    # TODO authorization
    def create(self, request, *args, **kwargs):
        data = request.data

        try:
            city_from, city_to, driver_id, vehicle_id, duration_data = self._extract_ride_data(data)

            city_from_obj, created = City.objects.get_or_create(
                **{'name': city_from['name'], 'county': city_from['county'], 'state': city_from['state']})
            city_to_obj, created = City.objects.get_or_create(
                **{'name': city_to['name'], 'county': city_to['county'], 'state': city_to['state']})

            # TODO in a future, driver will be passed with token
            driver = User.objects.get(user_id=driver_id)
            vehicle = Vehicle.objects.get(vehicle_id=vehicle_id, user_id=driver)

            duration = datetime.timedelta(hours=duration_data['hours'], minutes=duration_data['minutes'])
            ride = Ride(city_to=city_to_obj, city_from=city_from_obj, driver=driver, vehicle=vehicle, duration=duration,
                        **data)
        except KeyError as e:
            return JsonResponse(status=status.HTTP_400_BAD_REQUEST, data=f"Missing parameter {e}", safe=False)
        except User.DoesNotExist:
            return JsonResponse(status=status.HTTP_400_BAD_REQUEST, data=f"Driver not found", safe=False)
        except Vehicle.DoesNotExist:
            return JsonResponse(status=status.HTTP_400_BAD_REQUEST, data=f"Vehicle not found", safe=False)

        ride.save()
        serializer = self.get_serializer(ride)

        return JsonResponse(serializer.data, status=status.HTTP_200_OK, safe=False)

    # TODO authorization
    def update(self, request, *args, **kwargs):
        """
        Endpoint for updating Ride object.
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        if request.method == 'PATCH':
            instance = self.get_object()

            if not instance.passengers.filter(passenger__decision__in=['accepted', 'pending']):
                update_data = request.data
                instance = self._update_ride_nested_fields(update_data)

                serializer = self.get_serializer(instance=instance, data=update_data, partial=True)
                if serializer.is_valid():
                    serializer.save()
                    serializer = self.get_serializer(instance)
                    return JsonResponse(serializer.data, safe=False)

                return JsonResponse(status=status.HTTP_400_BAD_REQUEST, data="Wrong parameters", safe=False)
            else:
                return JsonResponse(status=status.HTTP_405_METHOD_NOT_ALLOWED, data="Cannot edit ride data", safe=False)

        return super().update(request, *args, **kwargs)

    # TODO authorization
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        # TODO check if user is a driver
        instance.is_cancelled = True
        instance.save()
        return JsonResponse(status=status.HTTP_200_OK, data=f'Ride successfully deleted.', safe=False)

    # TODO authorization
    @action(detail=False, methods=['get'], url_path=r'user_rides/(?P<user_id>[^/.]+)')
    def user_rides(self, request, user_id):
        """
        Endpoint for getting user rides. Can be filtered with price (from - to), from place, to place
        :param user_id:
        :param request:
        :return: List of user's rides.
        """

        try:
            driver = User.objects.get(user_id=user_id)
        except User.DoesNotExist:
            return JsonResponse(status=status.HTTP_404_NOT_FOUND, data="User not found", safe=False)

        queryset = self.get_queryset()
        rides = queryset.filter(driver=driver, start_date__gt=datetime.datetime.today())
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

    # TODO authorization
    @action(detail=True, methods=['post'])
    def send_request(self, request, pk=None):
        """
        Endpoint for sending request to join a ride.
        :param request:
        :param pk:
        :return:
        """
        parameters = request.data
        try:
            requesting_user = User.objects.get(user_id=parameters['requestor_id'])
            seats_no = parameters['seats']
        except User.DoesNotExist:
            return JsonResponse(status=status.HTTP_404_NOT_FOUND, data="User not found", safe=False)
        except KeyError as e:
            return JsonResponse(status=status.HTTP_400_BAD_REQUEST, data=f"Missing parameter: {e}", safe=False)

        instance = self.get_object()

        is_correct, message = verify_request(user=requesting_user, ride=instance, seats=seats_no)

        if is_correct:
            decision = Participation.Decision.ACCEPTED if instance.automatic_confirm else Participation.Decision.PENDING
            Participation.objects.create(ride=instance, user=requesting_user, decision=decision,
                                         reserved_seats=seats_no)
            return JsonResponse(status=status.HTTP_200_OK, data='Request successfully sent', safe=False)
        else:
            return JsonResponse(status=status.HTTP_400_BAD_REQUEST, data=message, safe=False)

    # TODO Authorization
    @action(detail=False, methods=['post'], url_path=r'request/(?P<request_id>[^/.]+)', )
    def request(self, request, request_id):
        """
        Endpoint for drivers to accept or decline pending requests.
        :param request:
        :param request_id:
        :return:
        """
        try:
            participation = Participation.objects.get(id=request_id)
        except Participation.DoesNotExist:
            return JsonResponse(status=status.HTTP_404_NOT_FOUND, data="Request not found", safe=False)

        data = request.data
        try:
            requesting_user = User.objects.get(user_id=data['driver_id'])
            if participation.ride.driver == requesting_user and participation.decision == participation.Decision.PENDING:
                decision = data['decision']
                if decision in [choice[0] for choice in Participation.Decision.choices]:
                    participation.decision = decision
                    participation.save()
                    return JsonResponse(status=status.HTTP_200_OK, data=f'Request successfully changed to {decision}',
                                        safe=False)
                else:
                    return JsonResponse(status=status.HTTP_400_BAD_REQUEST, data=f"Invalid decision parameter value",
                                        safe=False)
            return JsonResponse(status=status.HTTP_405_METHOD_NOT_ALLOWED,
                                data=f"Request do not have {participation.Decision.PENDING} status", safe=False)
        except User.DoesNotExist:
            return JsonResponse(status=status.HTTP_404_NOT_FOUND, data="User not found", safe=False)
        except KeyError as e:
            return JsonResponse(status=status.HTTP_400_BAD_REQUEST, data=f"Missing parameter: {e}", safe=False)

    # TODO Authorization
    @request.mapping.delete
    def delete_request(self, request, request_id):
        """
        Endpoint for removing sent requests
        :param request:
        :param request_id:
        :return:
        """

        try:
            participation = Participation.objects.get(id=request_id)
        except Participation.DoesNotExist:
            return JsonResponse(status=status.HTTP_404_NOT_FOUND, data="Request not found", safe=False)

        try:
            # TODO check if requesting user is a passenger of this participation
            if participation.decision != Participation.Decision.CANCELLED:
                participation.decision = Participation.Decision.CANCELLED
                participation.save()
                return JsonResponse(status=status.HTTP_200_OK, data=f'Request successfully cancelled ', safe=False)
            else:
                return JsonResponse(status=status.HTTP_405_METHOD_NOT_ALLOWED, data=f"Request is already cancelled",
                                    safe=False)
        except KeyError as e:
            return JsonResponse(status=status.HTTP_400_BAD_REQUEST, data=f"Missing parameter: {e}", safe=False)
