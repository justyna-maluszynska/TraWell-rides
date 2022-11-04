import datetime
from typing import List

from geopy import distance

from cities.models import City
from rides.models import Ride, Participation
from users.models import User
from vehicles.models import Vehicle

MAX_DISTANCE = 10


def validate_hours_minutes(hours: int, minutes: int):
    return 0 <= hours and 0 <= minutes < 60


def convert_duration(duration: dict) -> datetime.timedelta:
    return datetime.timedelta(hours=duration['hours'], minutes=duration['minutes'])


def validate_duration(value: dict) -> bool:
    try:
        hours = value['hours']
        minutes = value['minutes']
        if 0 > hours or 0 > minutes >= 60:
            return False
        return True
    except KeyError:
        return False


def get_duration(data: dict) -> datetime.timedelta or None:
    duration = None
    try:
        duration_data = data.pop('duration')
        if validate_duration(duration_data):
            duration = convert_duration(duration_data)
        return duration
    except KeyError:
        return duration


def calculate_distance(city_from: dict, city_to: City) -> float:
    """
    Calculates distance between two given cities
    :param city_from: first city
    :param city_to: second city
    :return: distance between two cities in km
    """
    coord_from = (city_from['lat'], city_from['lng'])
    coord_to = (city_to.lat, city_to.lng)
    return distance.distance(coord_from, coord_to).km


def get_city_info(parameters: dict, which_city: str) -> dict:
    """
    Converts parameters to more readable dictionary with city info.

    :param parameters: parameters from user
    :param which_city: from or to
    :return: dictionary with city data
    """
    return {"name": parameters[f'city_{which_city}'], "state": parameters[f'city_{which_city}_state'],
            "county": parameters[f'city_{which_city}_county'], "lat": parameters[f'city_{which_city}_lat'],
            "lng": parameters[f'city_{which_city}_lng']}


def find_city_object(city: dict) -> City | None:
    """
    Finds requested city in database and returns its object.

    :param city: dictionary with city data
    :return: found City object or None
    """
    try:
        city_obj = City.objects.get(name=city['name'], state=city['state'], county=city['county'])
        return city_obj
    except City.DoesNotExist:
        return None


def find_near_cities(city: dict) -> List[int]:
    """
    Finds cities in a MAX_DISTANCE ray from requested city.

    :param city: find near cities to this given City data dict
    :return: list with cities ids
    """
    queryset = City.objects.filter(county=city['county'])
    near_cities_ids = [near_city.city_id for near_city in queryset if
                       calculate_distance(city, near_city) <= MAX_DISTANCE]
    return near_cities_ids


def get_user_vehicle(data, user) -> Vehicle or None:
    vehicle = None
    try:
        vehicle_id = data.pop('vehicle')
        if user.private:
            vehicle = Vehicle.objects.get(vehicle_id=vehicle_id, user=user)
        return vehicle
    except KeyError or Vehicle.DoesNotExist:
        return vehicle


def filter_input_data(data: dict, expected_keys: list) -> dict:
    return {key: value for key, value in data.items() if key in expected_keys}


def filter_by_decision(decision, rides_ids, user):
    if decision in [Participation.Decision.PENDING, Participation.Decision.ACCEPTED, Participation.Decision.DECLINED]:
        print(decision)
        return Participation.objects.filter(ride__ride_id__in=rides_ids, user=user, decision=decision)
    return Participation.objects.filter(ride__ride_id__in=rides_ids, user=user)


def filter_rides_by_cities(request, queryset):
    try:
        city_from_dict = get_city_info(request.GET, 'from')
        queryset = queryset.filter(city_from__name=city_from_dict['name'], city_from__state=city_from_dict['state'],
                                   city_from__county=city_from_dict['county'])
    except KeyError:
        pass

    try:
        city_to_dict = get_city_info(request.GET, 'to')
        queryset = queryset.filter(city_to__name=city_to_dict['name'], city_to__state=city_to_dict['state'],
                                   city_to__county=city_to_dict['county'])
    except KeyError:
        pass

    return queryset


def verify_request(user: User, ride: Ride, seats: int) -> (bool, str):
    """
    Verify if requesting user can join specified ride.
    :param seats: Requested seats to book
    :param user: User requesting to join ride
    :param ride: Ride related to request
    :return: True if request can be sent, otherwise False and message with more info about verification
    """
    if ride.driver_id == user.user_id:
        return False, "Driver cannot send request to join his ride"
    if ride.passengers.filter(user_id=user.user_id, passenger__decision__in=[Participation.Decision.PENDING,
                                                                             Participation.Decision.ACCEPTED]):
        return False, "User is already in ride or waiting for decision"
    if 1 <= seats >= ride.available_seats:
        return False, "There are not enough seats"

    current_date = datetime.datetime.now(datetime.timezone.utc)
    if current_date > ride.start_date:
        return False, "Ride already started or is finished"

    return True, "OK"


def validate_values(vehicle, duration, serializer, user) -> (bool, str):
    if vehicle is None and user.private:
        return False, 'Vehicle parameter is invalid'
    if duration is None:
        return False, 'Duration parameter is invalid'
    if not serializer.is_valid():
        return False, serializer.errors
    return True, 'OK'
