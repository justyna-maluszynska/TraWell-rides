import random

from cities.models import City
from rides.factories import RideFactory
from users.models import User
from vehicles.models import Vehicle


def get_list_without_index(list, index):
    res = list[:]
    res.pop(index)
    return res


def create(amount):
    cities = City.objects.all()
    vehicles = Vehicle.objects.all()
    users = User.objects.all()
    for city_to_index in range(len(cities)):
        for i in range(amount):
            city_from = random.choice(get_list_without_index(cities, city_to_index))
            city_to = cities[city_to_index]
            driver_index = random.choice(range(len(users)))
            driver = users[driver_index]
            vehicle = random.choice(vehicles)
            seats = random.randint(1, 9)
            passengers = random.choices(get_list_without_index(users, driver_index), k=random.randint(0, seats))

            RideFactory(city_from=city_from, city_to=city_to, driver=driver, vehicle=vehicle, seats=seats, passengers=passengers)