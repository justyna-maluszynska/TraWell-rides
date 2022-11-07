import factory.django
import pytz
from factory import fuzzy

from cities.factories import CityFactory
from users.factories import UserFactory
from vehicles.factories import VehicleFactory
from . import models


class RideFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Ride

    city_from = factory.SubFactory(CityFactory)
    city_to = factory.SubFactory(CityFactory)
    area_from = factory.Faker('text', max_nb_chars=100)
    area_to = factory.Faker('text', max_nb_chars=100)
    start_date = factory.Faker('future_datetime', tzinfo=pytz.timezone('Europe/Warsaw'))
    duration = factory.Faker('time_delta', end_datetime=start_date)
    price = factory.Faker('pydecimal', left_digits=4, right_digits=2, positive=True)
    seats = factory.Faker('random_digit_not_null')
    recurrent = False
    automatic_confirm = factory.Faker('pybool')
    description = factory.Faker('text', max_nb_chars=300)
    driver = factory.SubFactory(UserFactory)
    vehicle = factory.SubFactory(VehicleFactory)
    is_cancelled = False
    recurrent_ride = None


class ParticipationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Participation

    ride = factory.SubFactory(RideFactory)
    user = factory.SubFactory(UserFactory)
    decision = factory.fuzzy.FuzzyChoice(['accepted', 'pending', 'cancelled', 'declined'])
    reserved_seats = factory.fuzzy.FuzzyChoice([1, 2, 3])


class RideWithPassengerFactory(RideFactory):
    participation = factory.RelatedFactory(ParticipationFactory, factory_related_name='ride',
                                           **{'decision': 'pending'})


class RideWith2PassengersFactory(RideFactory):
    participation1 = factory.RelatedFactory(ParticipationFactory, factory_related_name='ride')
    participation2 = factory.RelatedFactory(ParticipationFactory, factory_related_name='ride')
