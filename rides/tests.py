import requests
from django.test import TestCase
from rest_framework.test import APIClient

from rides.factories import RideFactory, ParticipationFactory, RideWithPassengerFactory
from rides.models import Ride, Participation

AUTH_TOKEN = "Bearer eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICJleUhzZzNlRkdiQzdTWjRQOEtWYXQ2aWJDLVlJWmE2dU03RnYycTdWQWhvIn0.eyJleHAiOjE2Njc2MTY4MTYsImlhdCI6MTY2NzU5ODgxNiwiYXV0aF90aW1lIjoxNjY3NTk4ODE2LCJqdGkiOiJlZDliNjU5Mi1hOWU2LTRhMTItOTIzYi0wZDhkNjZjYTBhNDAiLCJpc3MiOiJodHRwOi8vbG9jYWxob3N0Ojg0MDMvYXV0aC9yZWFsbXMvVHJhV2VsbCIsImF1ZCI6WyJzb2NpYWwtb2F1dGgiLCJyZWFjdCIsImFjY291bnQiXSwic3ViIjoiZmMwZjRlZTAtNzAzYS00ZTkwLWEwZTQtODdjMzIzMjkyNTk5IiwidHlwIjoiQmVhcmVyIiwiYXpwIjoia3Jha2VuZCIsInNlc3Npb25fc3RhdGUiOiJhYWMwZTY4Mi05MjdiLTRhMTItOTFmNi01ODQ0MTIwZjM2ZDYiLCJhY3IiOiIxIiwiYWxsb3dlZC1vcmlnaW5zIjpbImh0dHA6Ly9sb2NhbGhvc3Q6OTAwMCJdLCJyZWFsbV9hY2Nlc3MiOnsicm9sZXMiOlsib2ZmbGluZV9hY2Nlc3MiLCJ1bWFfYXV0aG9yaXphdGlvbiIsImFwcC11c2VyIiwicHJpdmF0ZV91c2VyIiwiZGVmYXVsdC1yb2xlcy10cmF3ZWxsIl19LCJyZXNvdXJjZV9hY2Nlc3MiOnsic29jaWFsLW9hdXRoIjp7InJvbGVzIjpbInVzZXIiXX0sImtyYWtlbmQiOnsicm9sZXMiOlsidXNlciJdfSwicmVhY3QiOnsicm9sZXMiOlsidXNlciJdfSwiYWNjb3VudCI6eyJyb2xlcyI6WyJtYW5hZ2UtYWNjb3VudCIsIm1hbmFnZS1hY2NvdW50LWxpbmtzIiwidmlldy1wcm9maWxlIl19fSwic2NvcGUiOiJvcGVuaWQgcHJvZmlsZSBlbWFpbCIsInNpZCI6ImFhYzBlNjgyLTkyN2ItNGExMi05MWY2LTU4NDQxMjBmMzZkNiIsImVtYWlsX3ZlcmlmaWVkIjp0cnVlLCJ1c2VyX3R5cGUiOiJQcml2YXRlIEFjY291bnQiLCJkYXRlX29mX2JpcnRoIjoiMjAyMi0xMC0zMSIsImZhY2Vib29rIjoiIiwibmFtZSI6Imp1c3R5bmEgbWFsIiwicHJlZmVycmVkX3VzZXJuYW1lIjoiZm1hanJveEBnbWFpbC5jb20iLCJpbnN0YWdyYW0iOiIiLCJnaXZlbl9uYW1lIjoianVzdHluYSIsImZhbWlseV9uYW1lIjoibWFsIiwiZW1haWwiOiJmbWFqcm94QGdtYWlsLmNvbSJ9.QPh96_BLNHXdw_ICPIc5he5zQGXMXOrCrkz4OhCTibOYlc19li6wuFXCpC1R9phjBMI8Yvs6ncJav0nycxaRjZJWLS5pdoUP3-jVCZtFDDsF0fpKHrCFT26t5IWUZhGtLsE37YXwOKm9mVc7PQdIcH7CnYro8bPfgyMYJ0kGIp0XWWGkOsTt-0VjrZiuU32mGcqhE5TZguNHdzr2g6Y1rgu_wHHdaDzwub55LSp1g0AJUAXaW8cgN_KH-r4XcTgJ-7vmRn5KiGngijhESiNl_Li3axvTepDzEyFAYiaI1Wjk7NAmKRexJJRQ3hUO6BBu0-txZrgBbjPclb3L7R1H2g"


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

    def test_can_driver_edit(self):
        ride_factory = RideFactory.create(seats=5)
        ride = Ride.objects.get(ride_id=ride_factory.ride_id)
        self.assertEqual(ride.can_driver_edit, True)

        for decision in [Participation.Decision.ACCEPTED, Participation.Decision.PENDING]:
            participation = ParticipationFactory.create(ride=ride_factory, decision=decision, reserved_seats=1)
            self.assertEqual(ride.can_driver_edit, False)

            participation.decision = Participation.Decision.CANCELLED
            participation.save()
            self.assertEqual(ride.can_driver_edit, True)


class RideViewSetTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=AUTH_TOKEN)

    def test_returns_details_for_not_authorized_user(self):
        self.client.credentials()
        ride_factory = RideFactory()

        response = self.client.get(f"/rides/{ride_factory.ride_id}/")
        results = response.data

        self.assertEqual(response.status_code, 200)
        self.assertEqual(results['ride_id'], ride_factory.ride_id)

    def test_returns_details_for_authorized_user(self):
        ride_factory = RideWithPassengerFactory()

        response = self.client.get(f"/rides/{ride_factory.ride_id}/")
        self.assertEqual(response.status_code, 200)
        results = response.data

        self.assertEqual(results['ride_id'], ride_factory.ride_id)

    def test_get_not_existing_ride(self):
        response = self.client.get(f"/rides/1/")
        self.assertEqual(response.status_code, 404)
