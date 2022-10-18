from typing import List

from geopy import distance

from cities.models import City

MAX_DISTANCE = 10


def validate_hours_minutes(hours: int, minutes: int):
    return 0 <= hours and 0 <= minutes < 60


def calculate_distance(city_from: dict, city_to: City):
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
        city_obj = City.objects.filter(name=city['name'], state=city['state'], county=city['county']).first()
        return city_obj
    except City.DoesNotExist:
        return None


def find_near_cities(city: dict) -> List[int]:
    """
    Finds cities in a MAX_DISTANCE ray from requested city.

    :param city: find near cities to this given City data dict
    :return: list with cities ids
    """
    queryset = City.objects.filter(state=city['county'])
    near_cities_ids = [near_city.city_id for near_city in queryset if
                       calculate_distance(city, near_city) <= MAX_DISTANCE]
    return near_cities_ids
