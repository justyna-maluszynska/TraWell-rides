import datetime
import json

import factory
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from cities.factories import CityFactory
from cities.models import City
from rides.factories import RideFactory, ParticipationFactory, RideWithPassengerFactory
from rides.models import Ride, Participation
from users.factories import UserFactory
from vehicles.factories import VehicleFactory

AUTH_TOKEN = "Bearer eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICJleUhzZzNlRkdiQzdTWjRQOEtWYXQ2aWJDLVlJWmE2dU03RnYycTdWQWhvIn0.eyJleHAiOjE2Njc4NzAwNTksImlhdCI6MTY2Nzg1MjA1OSwiYXV0aF90aW1lIjoxNjY3ODUyMDU5LCJqdGkiOiIxNzQ5NmE4NS1lZjI0LTRiMDgtOWY0OS1kNWYyNDcyZTA4OGYiLCJpc3MiOiJodHRwOi8vbG9jYWxob3N0Ojg0MDMvYXV0aC9yZWFsbXMvVHJhV2VsbCIsImF1ZCI6WyJzb2NpYWwtb2F1dGgiLCJyZWFjdCIsImFjY291bnQiXSwic3ViIjoiZmMwZjRlZTAtNzAzYS00ZTkwLWEwZTQtODdjMzIzMjkyNTk5IiwidHlwIjoiQmVhcmVyIiwiYXpwIjoia3Jha2VuZCIsInNlc3Npb25fc3RhdGUiOiI1OTVhNTg0MC1hNWNkLTQzYWItYmIzMC03YWFiOTE3ZTkxNzgiLCJhY3IiOiIxIiwiYWxsb3dlZC1vcmlnaW5zIjpbImh0dHA6Ly9sb2NhbGhvc3Q6OTAwMCJdLCJyZWFsbV9hY2Nlc3MiOnsicm9sZXMiOlsib2ZmbGluZV9hY2Nlc3MiLCJ1bWFfYXV0aG9yaXphdGlvbiIsImFwcC11c2VyIiwicHJpdmF0ZV91c2VyIiwiZGVmYXVsdC1yb2xlcy10cmF3ZWxsIl19LCJyZXNvdXJjZV9hY2Nlc3MiOnsic29jaWFsLW9hdXRoIjp7InJvbGVzIjpbInVzZXIiXX0sImtyYWtlbmQiOnsicm9sZXMiOlsidXNlciJdfSwicmVhY3QiOnsicm9sZXMiOlsidXNlciJdfSwiYWNjb3VudCI6eyJyb2xlcyI6WyJtYW5hZ2UtYWNjb3VudCIsIm1hbmFnZS1hY2NvdW50LWxpbmtzIiwidmlldy1wcm9maWxlIl19fSwic2NvcGUiOiJvcGVuaWQgcHJvZmlsZSBlbWFpbCIsInNpZCI6IjU5NWE1ODQwLWE1Y2QtNDNhYi1iYjMwLTdhYWI5MTdlOTE3OCIsImVtYWlsX3ZlcmlmaWVkIjp0cnVlLCJ1c2VyX3R5cGUiOiJQcml2YXRlIEFjY291bnQiLCJkYXRlX29mX2JpcnRoIjoiMjAyMi0xMC0zMSIsImZhY2Vib29rIjoiIiwibmFtZSI6Imp1c3R5bmEgbWFsIiwicHJlZmVycmVkX3VzZXJuYW1lIjoiZm1hanJveEBnbWFpbC5jb20iLCJpbnN0YWdyYW0iOiIiLCJnaXZlbl9uYW1lIjoianVzdHluYSIsImZhbWlseV9uYW1lIjoibWFsIiwiZW1haWwiOiJmbWFqcm94QGdtYWlsLmNvbSJ9.aOP7wCswf2UK7udIdy75hP1iu7ZonbA8CZFjv55T7Mel7XxxmxNl7dw1I0bIaG5et7E6pyf13yHJ5IGQQPz3JXZoOMxtco8alNL5hPd-0IL7gGh5Nl-uW4bbpuHjWka-eDy9bzbx8wV7-nE2lMnSP90lVpGaqpFQuY-sMId5mQF3kY54Sgn2_PSmQF47Mwo-F8UvllqwlrJZjiZbUILjdHSsPYc3pPejEaRl0JCKrg18dCvyjhvtVBq5cpeaBrdpRKtrjXl7mf6h2Bav62Jt-bajcRE_6aSGV1OacVbiyIHtAGi8VkQUhjInw_RTSprXSuOT-902mNIaqa-6Ogopxw"


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

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(results['ride_id'], ride_factory.ride_id)

    def test_returns_details_for_authorized_user(self):
        ride_factory = RideWithPassengerFactory()

        response = self.client.get(f"/rides/{ride_factory.ride_id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data

        self.assertEqual(results['ride_id'], ride_factory.ride_id)

    def test_get_not_existing_ride(self):
        response = self.client.get(f"/rides/1/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

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
        self.assertEqual(json.loads(response.content), {'city_from': ['This field is required.']})

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
        self.assertEqual(json.loads(response.content), "Duration parameter is invalid")

    def test_post_ride_vehicle_do_not_belong_to_user(self):
        post_data = prepare_data_for_post()
        vehicle = VehicleFactory.create()
        post_data['vehicle'] = vehicle.vehicle_id

        response = self.client.post(f"/rides/", data=post_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(json.loads(response.content), "Vehicle parameter is invalid")

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
        self.assertEqual(json.loads(response.content), "Vehicle parameter is invalid")

    def test_post_calculates_available_seats(self):
        post_data = prepare_data_for_post()
        seats = post_data['seats']
        response = self.client.post(f"/rides/", data=post_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        content = json.loads(response.content)
        ride = Ride.objects.get(ride_id=content['ride_id'])
        self.assertEqual(seats, ride.available_seats)

    def test_partial_update_ride_successful(self):
        user = UserFactory(email='fmajrox@gmail.com', private=True)
        vehicle = VehicleFactory.create_batch(size=2, user=user)
        ride = RideWithPassengerFactory.create(seats=10, vehicle=vehicle[0], driver=user)
        patch_data = {'seats': 5, 'vehicle': vehicle[1].vehicle_id, 'description': 'updated description'}

        response = self.client.patch(f"/rides/{ride.ride_id}/", data=patch_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        ride_obj = Ride.objects.get(ride_id=ride.ride_id)

        self.assertEqual(ride_obj.seats, patch_data['seats'])
        self.assertEqual(ride_obj.description, patch_data['description'])
        self.assertEqual(ride_obj.vehicle.vehicle_id, patch_data['vehicle'])

    def test_partial_update_ride_company_user_successful(self):
        user = UserFactory(email='fmajrox@gmail.com', private=False)
        ride = RideWithPassengerFactory.create(seats=10, driver=user, automatic_confirm=True)
        patch_data = {'seats': 5, 'automatic_confirm': False, 'description': 'updated description'}

        response = self.client.patch(f"/rides/{ride.ride_id}/", data=patch_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        ride_obj = Ride.objects.get(ride_id=ride.ride_id)

        self.assertEqual(ride_obj.seats, patch_data['seats'])
        self.assertEqual(ride_obj.description, patch_data['description'])
        self.assertEqual(ride_obj.automatic_confirm, patch_data['automatic_confirm'])

    def test_full_update_ride_successful(self):
        ride_data = prepare_data_for_post()

        response = self.client.post(f"/rides/", data=ride_data, format='json')
        content = json.loads(response.content)
        ride = Ride.objects.get(ride_id=content['ride_id'])

        city_from = factory.build(dict, FACTORY_CLASS=CityFactory)
        city_to = factory.build(dict, FACTORY_CLASS=CityFactory)

        ride_data.update(
            {'city_from': city_from, 'city_to': city_to, 'price': 139.99, 'start_date': "2035-12-01T04:00:22Z",
             'coordinates': [{'lat': 108.765432, 'lng': 45.565655, 'sequence_no': 1}], 'seats': 99,
             "duration": {"hours": 6, "minutes": 36}, })

        patch_response = self.client.patch(f"/rides/{ride.ride_id}/", data=ride_data, format='json')
        self.assertEqual(patch_response.status_code, status.HTTP_200_OK)

        ride_after_update = Ride.objects.get(ride_id=content['ride_id'])
        self.assertEqual(ride_after_update.city_from.name, city_from['name'])
        self.assertEqual(ride_after_update.city_to.name, city_to['name'])
        self.assertEqual(len(ride_after_update.coordinates.all()), len(ride_data['coordinates']))
        self.assertEqual(float(ride_after_update.price), ride_data['price'])
        self.assertEqual(ride_after_update.start_date.isoformat()[:-6] + 'Z', ride_data['start_date'])
        self.assertEqual(ride_after_update.seats, ride_data['seats'])
        self.assertEqual(ride_after_update.duration, datetime.timedelta(hours=ride_data['duration']['hours'],
                                                                        minutes=ride_data['duration']['minutes']))

    def test_patch_do_not_allow_incorrect_seats(self):
        user = UserFactory(email='fmajrox@gmail.com', private=True)
        vehicle = VehicleFactory.create_batch(size=2, user=user)
        ride = RideWithPassengerFactory.create(seats=10, vehicle=vehicle[0], driver=user,
                                               participation__reserved_seats=5)
        patch_data = {'seats': 1, 'vehicle': vehicle[1].vehicle_id, 'description': 'updated description'}

        response = self.client.patch(f"/rides/{ride.ride_id}/", data=patch_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(json.loads(response.content), "Invalid seats parameter")

    def test_delete_ride_successfully(self):
        vehicle = VehicleFactory.create(user__email='fmajrox@gmail.com')
        ride = RideWithPassengerFactory.create(seats=2, vehicle=vehicle, driver=vehicle.user)

        response = self.client.delete(f"/rides/{ride.ride_id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        ride_obj = Ride.objects.get(ride_id=ride.ride_id)
        self.assertEqual(ride_obj.is_cancelled, True)

        response = self.client.get(f'/rides/{ride.ride_id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_ride_not_allowed(self):
        UserFactory.create(email='fmajrox@gmail.com')
        ride = RideFactory.create()

        response = self.client.delete(f"/rides/{ride.ride_id}/")

        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(json.loads(response.content), "User not allowed to delete ride")
