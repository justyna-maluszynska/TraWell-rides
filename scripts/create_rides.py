import datetime
import random

from cities.models import City
from rides.factories import RideWithPassengerFactory
from rides_microservice import tasks
from rides_microservice.celery import queue_notify, queue_reviews
from users.models import User
from rides.serializers import RideSerializer


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
            duration = datetime.timedelta(hours=random.randint(1, 23))

            ride = RideWithPassengerFactory(city_from=city_from, city_to=city_to, driver=driver, vehicle=vehicle, seats=seats, duration=duration)

            tasks.publish_message(RideSerializer(ride).data, 'rides.create', queue_notify, 'notify')
            tasks.publish_message(RideSerializer(ride).data, 'rides.create', queue_reviews, 'review')
