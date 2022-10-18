import factory.django

from . import models


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.User

    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    avg_rate = factory.Faker('random_element', elements=list(map(lambda x: x/10 if x > 9 else None, list(range(9, 51)))))