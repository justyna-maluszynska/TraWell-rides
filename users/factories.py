import factory.django

from . import models


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.User

    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    avg_rate = factory.Faker('pydecimal', left_digits=1, right_digits=2, min_value=1, max_value=5)
    private = factory.Faker('pybool')
