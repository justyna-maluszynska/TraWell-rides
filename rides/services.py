from rides.models import Ride


def create_ride(data):
    ride = Ride(**data)
    ride.save()
