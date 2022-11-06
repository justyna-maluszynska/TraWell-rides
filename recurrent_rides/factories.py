import datetime

import factory
import pytz
from factory import fuzzy

from cities.factories import CityFactory
from users.factories import UserFactory
from vehicles.factories import VehicleFactory
from . import models


class RecurrentRideFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.RecurrentRide

    city_from = factory.SubFactory(CityFactory)
    city_to = factory.SubFactory(CityFactory)
    area_from = factory.Faker('text', max_nb_chars=100)
    area_to = factory.Faker('text', max_nb_chars=100)
    start_date = factory.Faker('future_datetime', tzinfo=pytz.timezone('Europe/Warsaw'))
    end_date = factory.Faker('date_time_between', start_date=start_date,
                             end_date=datetime.datetime(2022, 6, 20, 12, 12, 12), tzinfo=pytz.timezone('Europe/Warsaw'))
    frequency_type = factory.fuzzy.FuzzyChoice(choices=['daily', 'hourly', 'monthly'])
    frequence = factory.Faker('random_digit_not_null')
    occurrences = None
    duration = factory.Faker('time_delta', end_datetime=start_date)
    price = factory.Faker('pydecimal', left_digits=4, right_digits=2, positive=True)
    seats = factory.Faker('random_digit_not_null')
    automatic_confirm = factory.Faker('pybool')
    description = factory.Faker('text', max_nb_chars=300)
    driver = factory.SubFactory(UserFactory)
    vehicle = factory.SubFactory(VehicleFactory)
    is_cancelled = False
