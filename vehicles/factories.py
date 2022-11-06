import factory.django

from users.factories import UserFactory
from . import models

vehicles_makes = ['audi', 'bmw', 'citroen', 'dacia', 'dodge', 'fiat', 'ford', 'hyundai', 'kia', 'mercedes', 'nissan',
             'opel', 'peugeot', 'renault', 'seat', 'skoda', 'toyota', 'volkswagen', 'volvo']
vehicles_models = ['allroad', 'quattro', 'visa', 'xantia', 'mustang', 'mondeo', 'sierra', 'tempo', 'vectra', 'megane',
          'premium', 'bora', 'golf', 'polo', 'up!', 'maluch']


class VehicleFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Vehicle

    make = factory.Faker('random_element', elements=vehicles_makes)
    model = factory.Faker('random_element', elements=vehicles_models)
    color = factory.Faker('safe_color_name')
    user = factory.SubFactory(UserFactory)
