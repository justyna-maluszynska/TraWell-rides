from users.factories import UserFactory


def create(amount):
    for user in range(amount):
        UserFactory()