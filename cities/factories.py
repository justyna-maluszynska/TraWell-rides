import factory.django

from . import models


class CityFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.City

    name = factory.Faker('city')
    county = factory.Faker('country')
    state = factory.Faker('state')
    lat = factory.Faker('latitude')
    lng = factory.Faker('longitude')
