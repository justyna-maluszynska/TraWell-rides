from vehicles.factories import VehicleFactory


def create(amount):
    for vehicle in range(amount):
        VehicleFactory()

