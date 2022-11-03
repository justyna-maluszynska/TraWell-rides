from django.test import TestCase

from rides.factories import RideFactory, ParticipationFactory
from rides.models import Ride, Participation


class RideModelTests(TestCase):
    def test_ride_default_available_seats(self):
        ride_factory = RideFactory.create(seats=5)
        ride = Ride.objects.get(ride_id=ride_factory.ride_id)

        self.assertEqual(ride.available_seats, 5)

    def test_updates_available_seats(self):
        ride_factory = RideFactory.create(seats=5)
        participation1 = ParticipationFactory.create(ride=ride_factory, decision=Participation.Decision.ACCEPTED,
                                                     reserved_seats=2)
        ride = Ride.objects.get(ride_id=ride_factory.ride_id)

        self.assertEqual(ride.available_seats, 3)

        participation2 = ParticipationFactory.create(ride=ride_factory, decision=Participation.Decision.PENDING,
                                                     reserved_seats=1)
        ride.refresh_from_db()
        self.assertEqual(ride.available_seats, 2)

        participation1.decision = Participation.Decision.CANCELLED
        participation1.save()
        ride.refresh_from_db()
        self.assertEqual(ride.available_seats, 4)

        participation2.decision = Participation.Decision.CANCELLED
        participation2.save()
        ride.refresh_from_db()
        self.assertEqual(ride.available_seats, 5)
