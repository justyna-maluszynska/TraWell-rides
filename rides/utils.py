from geopy import distance

from cities.models import City


def validate_hours_minutes(hours: int, minutes: int):
    return 0 <= hours and 0 <= minutes < 60


def calculate_distance(city_from: dict, city_to: City):
    coord_from = (city_from['lat'], city_from['lng'])
    coord_to = (city_to.lat, city_to.lng)
    return distance.distance(coord_from, coord_to).km
