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


def extract_values(data: dict, expected_keys: list, user: User) -> (dict, Vehicle, datetime.timedelta):
    cleared_data = filter_input_data(data, expected_keys=expected_keys)

    vehicle = user_vehicle(data=cleared_data, user=user)
    duration = get_duration(cleared_data)

    if user.private:
        cleared_data['automatic_confirm'] = False

    return cleared_data, vehicle, duration


def create_or_update_ride(data: dict, keys: list, user: User, serializer: RideSerializer or RecurrentRideSerializer,
                          partial: bool = False, instance=None):
    cleared_data, vehicle, duration = extract_values(data, keys, user)
    if partial:
        context = {'driver': user, 'vehicle': vehicle}
    else:
        context = {'driver': user, 'vehicle': vehicle, 'duration': duration}
    serializer = serializer(instance=instance, data=cleared_data, partial=partial, context=context)
    is_valid, message = validate_values(vehicle=vehicle, duration=duration, serializer=serializer, user=user,
                                        partial=partial)

    if not is_valid:
        return status.HTTP_400_BAD_REQUEST, message

    serializer.save()
    return status.HTTP_200_OK, serializer.data


def update_partial_ride(instance, serializer, update_data, user):
    if user.private:
        expected_keys = ['seats', 'vehicle', 'description']
    else:
        expected_keys = ['seats', 'automatic_confirm', 'description']

    if not verify_available_seats(instance=instance, data=update_data):
        return status.HTTP_400_BAD_REQUEST, "Invalid seats parameter"

    return create_or_update_ride(data=update_data, keys=expected_keys, user=user, serializer=serializer,
                                 instance=instance, partial=True)


def update_whole_ride(instance, serializer, update_data, user):
    keys = ['city_from', 'city_to', 'area_from', 'area_to', 'start_date',
            'price', 'seats', 'vehicle', 'duration', 'description',
            'coordinates', 'automatic_confirm']
    return create_or_update_ride(data=update_data, keys=keys, user=user, serializer=serializer, instance=instance)


def cancel_ride(ride: Ride or RecurrentRide):
    ride.is_cancelled = True
    ride.save()
