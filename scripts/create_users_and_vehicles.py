from vehicles.factories import VehicleFactory


def create(amount):
    for _ in range(amount):
        VehicleFactory()
