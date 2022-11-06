import random

from cities.models import City
from recurrent_rides.factories import RecurrentRideFactory
from users.models import User


def get_list_without_index(list, index):
    res = list[:]
    res.pop(index)
    return res


def create(amount):
    cities = City.objects.all()
    users = User.objects.filter(vehicles__isnull=False)
    for city_to_index in range(len(cities)):
        for i in range(amount):
            city_from = random.choice(get_list_without_index(cities, city_to_index))
            city_to = cities[city_to_index]
            driver_index = random.choice(range(len(users)))
            driver = users[driver_index]
            vehicle = driver.vehicles.all()[0]
            seats = random.randint(1, 9)

            RecurrentRideFactory(city_from=city_from, city_to=city_to, driver=driver, vehicle=vehicle, seats=seats)
