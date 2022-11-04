import datetime

from rest_framework import status

from rides.serializers import RideSerializer, RecurrentRideSerializer
from rides.utils.utils import validate_values, get_user_vehicle, filter_input_data, get_duration
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
