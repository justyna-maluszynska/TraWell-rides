import datetime

import factory
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from cities.factories import CityFactory
from cities.models import City
from rides.factories import RideFactory, ParticipationFactory, RideWithPassengerFactory
from rides.models import Ride, Participation
from vehicles.factories import VehicleFactory

AUTH_TOKEN = "Bearer eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICJleUhzZzNlRkdiQzdTWjRQOEtWYXQ2aWJDLVlJWmE2dU03RnYycTdWQWhvIn0.eyJleHAiOjE2Njc3ODUyMjMsImlhdCI6MTY2Nzc2NzIyMywiYXV0aF90aW1lIjoxNjY3NzY3MjIzLCJqdGkiOiI3OWM1Y2RjYi01MzFlLTRjMTUtOGQ0OC1iMDlmZDBlYWFkNGIiLCJpc3MiOiJodHRwOi8vbG9jYWxob3N0Ojg0MDMvYXV0aC9yZWFsbXMvVHJhV2VsbCIsImF1ZCI6WyJzb2NpYWwtb2F1dGgiLCJyZWFjdCIsImFjY291bnQiXSwic3ViIjoiZmMwZjRlZTAtNzAzYS00ZTkwLWEwZTQtODdjMzIzMjkyNTk5IiwidHlwIjoiQmVhcmVyIiwiYXpwIjoia3Jha2VuZCIsInNlc3Npb25fc3RhdGUiOiI3N2JjNzMxZi1mYjA0LTRkMGQtYTExOS0wYzM1YzY3YmZkNWQiLCJhY3IiOiIxIiwiYWxsb3dlZC1vcmlnaW5zIjpbImh0dHA6Ly9sb2NhbGhvc3Q6OTAwMCJdLCJyZWFsbV9hY2Nlc3MiOnsicm9sZXMiOlsib2ZmbGluZV9hY2Nlc3MiLCJ1bWFfYXV0aG9yaXphdGlvbiIsImFwcC11c2VyIiwicHJpdmF0ZV91c2VyIiwiZGVmYXVsdC1yb2xlcy10cmF3ZWxsIl19LCJyZXNvdXJjZV9hY2Nlc3MiOnsic29jaWFsLW9hdXRoIjp7InJvbGVzIjpbInVzZXIiXX0sImtyYWtlbmQiOnsicm9sZXMiOlsidXNlciJdfSwicmVhY3QiOnsicm9sZXMiOlsidXNlciJdfSwiYWNjb3VudCI6eyJyb2xlcyI6WyJtYW5hZ2UtYWNjb3VudCIsIm1hbmFnZS1hY2NvdW50LWxpbmtzIiwidmlldy1wcm9maWxlIl19fSwic2NvcGUiOiJvcGVuaWQgcHJvZmlsZSBlbWFpbCIsInNpZCI6Ijc3YmM3MzFmLWZiMDQtNGQwZC1hMTE5LTBjMzVjNjdiZmQ1ZCIsImVtYWlsX3ZlcmlmaWVkIjp0cnVlLCJ1c2VyX3R5cGUiOiJQcml2YXRlIEFjY291bnQiLCJkYXRlX29mX2JpcnRoIjoiMjAyMi0xMC0zMSIsImZhY2Vib29rIjoiIiwibmFtZSI6Imp1c3R5bmEgbWFsIiwicHJlZmVycmVkX3VzZXJuYW1lIjoiZm1hanJveEBnbWFpbC5jb20iLCJpbnN0YWdyYW0iOiIiLCJnaXZlbl9uYW1lIjoianVzdHluYSIsImZhbWlseV9uYW1lIjoibWFsIiwiZW1haWwiOiJmbWFqcm94QGdtYWlsLmNvbSJ9.XRwjr6JuB6snJDq5CuF4B72Ds4MCfGclgVCCeK1YFKCB1EtP80h8V8UFUatwodkGy4vdprWelKlJfiLLfI_6XFFmEpLmUMLfjp2BTyHOvJQY-uQBkfouf-42xGZBJFP4csOq0Gir4RDcMua5pt_Cws6z1wVaqoFCXnwCXCyNBM5SaAQF1gwFEp9MD--4ah6Js18my7OQZD5vz1ipQgc1S8o0FBJVBK5sAFyiDrnKbLuhOvK_EKDIDOrZcRF3mJrxCdRwAqh7WMMFsT2SfdFx44knDpXbZwtd4SL8HzsytCN7DLx5uHQ61Gv3O69NBIZxlW9TTIVHcQcD9ZOz2YKaMQ"


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


def convert_city_to_dict(city: City) -> dict:
    return {'name': city.name, 'county': city.county, 'state': city.state, 'lat': city.lat, 'lng': city.lng}


def prepare_data_for_post(user_private: bool = True) -> dict:
    cities = CityFactory.create_batch(size=2)
    vehicle = VehicleFactory(**{'user__email': 'fmajrox@gmail.com', 'user__private': user_private})
    hours, minutes = 2, 30
    init_values = {'city_from': cities[0], 'city_to': cities[1], 'vehicle': vehicle,
                   'duration': datetime.timedelta(hours=hours, minutes=minutes)}
    post_data = factory.build(dict, FACTORY_CLASS=RideFactory, **init_values)
    post_data.pop('driver')
    post_data.update({'city_from': convert_city_to_dict(init_values['city_from']),
                      'city_to': convert_city_to_dict(init_values['city_to']),
                      'duration': {'hours': hours, 'minutes': minutes}, 'vehicle': vehicle.vehicle_id,
                      'coordinates': []})

    return post_data


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

    def test_post_ride_for_not_authorized_user(self):
        self.client.credentials()
        post_data = prepare_data_for_post()

        response = self.client.post(f"/rides/", data=post_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_post_ride_successful(self):
        post_data = prepare_data_for_post()

        response = self.client.post(f"/rides/", data=post_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_post_ride_missing_parameters(self):
        post_data = prepare_data_for_post()
        post_data.pop('city_from')

        response = self.client.post(f"/rides/", data=post_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_ride_creates_new_ride_and_cities(self):
        rides_before_post = len(Ride.objects.all())
        cities_before_post = len(City.objects.all())
        self.assertEqual(rides_before_post, 0)
        self.assertEqual(cities_before_post, 0)

        post_data = prepare_data_for_post()

        response = self.client.post(f"/rides/", data=post_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        rides_after_post = len(Ride.objects.all())
        cities_after_post = len(City.objects.all())
        self.assertEqual(rides_after_post, 1)
        self.assertEqual(cities_after_post, 2)

    def test_post_ride_incorrect_data(self):
        post_data = prepare_data_for_post()
        post_data['duration']['hours'] = -2

        response = self.client.post(f"/rides/", data=post_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_ride_vehicle_do_not_belong_to_user(self):
        post_data = prepare_data_for_post()
        vehicle = VehicleFactory.create()
        post_data['vehicle'] = vehicle.vehicle_id

        response = self.client.post(f"/rides/", data=post_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_ride_company_user(self):
        post_data = prepare_data_for_post(user_private=False)

        response = self.client.post(f"/rides/", data=post_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_post_ride_company_user_without_vehicle(self):
        post_data = prepare_data_for_post(user_private=False)
        post_data['vehicle'] = None

        response = self.client.post(f"/rides/", data=post_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_post_ride_company_user_without_automatic_confirm(self):
        post_data = prepare_data_for_post(user_private=False)
        post_data.pop('automatic_confirm')

        response = self.client.post(f"/rides/", data=post_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_post_ride_private_user_without_vehicle(self):
        post_data = prepare_data_for_post()
        post_data['vehicle'] = None

        response = self.client.post(f"/rides/", data=post_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
