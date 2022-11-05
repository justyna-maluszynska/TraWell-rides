from cities.models import City
from users.models import User
from utils.utils import find_near_cities
from vehicles.models import Vehicle


def city_object(city: dict) -> City | None:
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


def rides_with_cities_nearby(queryset, city_to: City, city_from: dict):
    """
    Finds rides starting from cities nearby city_to.

    :param queryset:
    :param city_to:
    :param city_from:
    :return:
    """
    queryset = queryset.filter(city_to__name=city_to.name, city_to__state=city_to.state, city_to__county=city_to.county,
                               available_seats__gt=0)

    if not queryset.exists():
        # There are no rides to given city destination, no sense to check the rest of parameters
        return queryset

    near_cities_ids = find_near_cities(city_from)

    queryset_with_near_cities = queryset.filter(city_from__city_id__in=near_cities_ids)
    return queryset_with_near_cities


def user_vehicle(data: dict, user: User) -> Vehicle or None:
    """
    Finds vehicle with given id, that belongs to given user.

    :param data: dictionary containing vehicle id
    :param user: owner of vehicle
    :return: found Vehicle object or None
    """
    try:
        vehicle = None
        vehicle_id = data.pop('vehicle')
        if user.private:
            vehicle = Vehicle.objects.get(vehicle_id=vehicle_id, user=user)
        return vehicle
    except KeyError or Vehicle.DoesNotExist:
        return None
