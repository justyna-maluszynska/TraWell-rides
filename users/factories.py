import factory.django

from . import models


urls = ['https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQm1V8v8tE0A-u0d980NqucUK343r3yEH3O9A&usqp=CAU'
        'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRzkw8ss5D9M_1S8TFry9umUGClpjt7W_vzbQ&usqp=CAU',
        'https://simg.nicepng.com/png/small/149-1494118_memes-derp-face-meme-png-facepalm-meme-png.png',
        '']


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.User

    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    email = factory.Sequence(lambda n: f'first_name-{n}@gmail.com')
    avg_rate = factory.Faker('pydecimal', left_digits=1, right_digits=2, min_value=1, max_value=5)
    private = factory.Faker('pybool')
    avatar = factory.Faker('random_element', elements=urls)
