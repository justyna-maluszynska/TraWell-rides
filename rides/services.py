import datetime

from rest_framework import status

from rides.models import Ride, RecurrentRide
from rides.serializers import RideSerializer, RecurrentRideSerializer
from rides.utils.utils import validate_values, get_user_vehicle, filter_input_data, get_duration, verify_available_seats
from users.models import User
from vehicles.models import Vehicle


def extract_post_values(data: dict, expected_keys: list, user: User) -> (dict, Vehicle, datetime.timedelta):
    cleared_data = filter_input_data(data, expected_keys=expected_keys)

    vehicle = get_user_vehicle(data=cleared_data, user=user)
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
        vehicle = get_user_vehicle(data=update_data, user=user)
        context['vehicle'] = vehicle
    else:
        expected_keys = ['seats', 'automatic_confirm', 'description']

    cleared_data = filter_input_data(update_data, expected_keys=expected_keys)
    if verify_available_seats(instance=instance, data=cleared_data):
        return status.HTTP_400_BAD_REQUEST, "Invalid seats parameter"

    return update_using_serializer(instance=instance, serializer=serializer, data=cleared_data, context=context)


def update_whole_ride(instance, serializer, update_data, user):
    cleared_data = filter_input_data(update_data,
                                     expected_keys=['city_from', 'city_to', 'area_from', 'area_to', 'start_date',
                                                    'price', 'seats', 'vehicle', 'duration', 'description',
                                                    'coordinates', 'automatic_confirm'])

    context = {}
    vehicle = get_user_vehicle(data=cleared_data, user=user)
    if user.private:
        context['vehicle'] = vehicle

    duration = get_duration(cleared_data)
    if duration is not None:
        context['duration'] = duration

    if user.private:
        cleared_data['automatic_confirm'] = False

    return update_using_serializer(instance=instance, serializer=serializer, data=cleared_data, context=context)
