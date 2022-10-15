import factory.django

from cities.CityFactory import CityFactory
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
    start_date = factory.Faker('future_datetime')
    end_date = factory.Faker('future_datetime')
    price = factory.Faker('random_element', elements=list(map(lambda x: x/100, list(range(1, 100001)))))
    seats = factory.Faker('random_digit_not_null')
    recurrent = factory.Faker('pybool')
    automatic_confirm = factory.Faker('pybool')
    description = factory.Faker('text', max_nb_chars=300)
    driver = factory.SubFactory(UserFactory)
    vehicle = factory.SubFactory(VehicleFactory)

    @factory.post_generation
    def passengers(self, create, extracted):
        if not create:
            return

        if extracted:
            for passenger in extracted:
                self.passengers.add(passenger)