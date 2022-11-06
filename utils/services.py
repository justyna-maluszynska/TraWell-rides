import datetime

from rest_framework import status

from recurrent_rides.models import RecurrentRide
from recurrent_rides.serializers import RecurrentRideSerializer
from rides.models import Ride
from rides.serializers import RideSerializer
from users.models import User
from utils.selectors import user_vehicle
from utils.utils import validate_values, filter_input_data, get_duration, verify_available_seats
from vehicles.models import Vehicle


def extract_post_values(data: dict, expected_keys: list, user: User) -> (dict, Vehicle, datetime.timedelta):
    cleared_data = filter_input_data(data, expected_keys=expected_keys)

    vehicle = user_vehicle(data=cleared_data, user=user)
    duration = get_duration(cleared_data)

    if user.private:
        cleared_data['automatic_confirm'] = False

    return cleared_data, vehicle, duration


def create_new_ride(data: dict, keys: list, user: User, serializer: RideSerializer or RecurrentRideSerializer):
    cleared_data, vehicle, duration = extract_post_values(data, keys, user)
    serializer = serializer(data=cleared_data, context={'driver': user, 'vehicle': vehicle, 'duration': duration})
    is_valid, message = validate_values(vehicle=vehicle, duration=duration, serializer=serializer, user=user)

    if not is_valid:
        return status.HTTP_400_BAD_REQUEST, message

    serializer.save()
    return status.HTTP_200_OK, serializer.data


def update_using_serializer(instance: Ride or RecurrentRide, serializer: RideSerializer or RecurrentRideSerializer,
                            data, context):
    serializer = serializer(instance=instance, data=data, partial=True)

    if serializer.is_valid():
        serializer.update(instance=instance, validated_data=data, partial=True, context=context)
        return status.HTTP_200_OK, serializer.data

    return status.HTTP_400_BAD_REQUEST, serializer.errors


def update_partial_ride(instance, serializer, update_data, user):
    context = {}

    if user.private:
        expected_keys = ['seats', 'vehicle', 'description']
        vehicle = user_vehicle(data=update_data, user=user)
        context['vehicle'] = vehicle
    else:
        expected_keys = ['seats', 'automatic_confirm', 'description']

    cleared_data = filter_input_data(update_data, expected_keys=expected_keys)
    if not verify_available_seats(instance=instance, data=cleared_data):
        return status.HTTP_400_BAD_REQUEST, "Invalid seats parameter"

    return update_using_serializer(instance=instance, serializer=serializer, data=cleared_data, context=context)


def update_whole_ride(instance, serializer, update_data, user):
    cleared_data = filter_input_data(update_data,
                                     expected_keys=['city_from', 'city_to', 'area_from', 'area_to', 'start_date',
                                                    'price', 'seats', 'vehicle', 'duration', 'description',
                                                    'coordinates', 'automatic_confirm'])

    context = {}
    vehicle = user_vehicle(data=cleared_data, user=user)
    if user.private:
        context['vehicle'] = vehicle

    duration = get_duration(cleared_data)
    if duration is not None:
        context['duration'] = duration

    if user.private:
        cleared_data['automatic_confirm'] = False

    return update_using_serializer(instance=instance, serializer=serializer, data=cleared_data, context=context)


def cancel_ride(ride: Ride or RecurrentRide):
    ride.is_cancelled = True
    ride.save()
