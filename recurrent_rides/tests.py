import datetime
import json

import factory
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from cities.factories import CityFactory
from cities.models import City
from recurrent_rides.factories import RecurrentRideFactory
from recurrent_rides.models import RecurrentRide
from rides.factories import ParticipationFactory
from rides.models import Ride, Participation
from rides.tests import convert_city_to_dict
from users.factories import UserFactory
from vehicles.factories import VehicleFactory

AUTH_TOKEN = "Bearer eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICJleUhzZzNlRkdiQzdTWjRQOEtWYXQ2aWJDLVlJWmE2dU03RnYycTdWQWhvIn0.eyJleHAiOjE2Njk3NzA0NDcsImlhdCI6MTY2OTc1MjQ0NywiYXV0aF90aW1lIjoxNjY5NzUyNDQ3LCJqdGkiOiIxY2IzNDU2Yy01Y2YwLTRmOTQtOTcxNS1hMTQ3MjhlYWRlMmMiLCJpc3MiOiJodHRwOi8vbG9jYWxob3N0Ojg0MDMvYXV0aC9yZWFsbXMvVHJhV2VsbCIsImF1ZCI6WyJzb2NpYWwtb2F1dGgiLCJyZWFjdCIsImFjY291bnQiXSwic3ViIjoiN2FkNWFkZjctOWM2ZS00YjhhLThjNWYtM2ZlOWZjMTNlY2IyIiwidHlwIjoiQmVhcmVyIiwiYXpwIjoia3Jha2VuZCIsInNlc3Npb25fc3RhdGUiOiIxYjAwNDJhZC1lMDAxLTQ3MjAtOWFhYy02MmM1MmE4NDg1OGEiLCJhY3IiOiIxIiwiYWxsb3dlZC1vcmlnaW5zIjpbImh0dHA6Ly9sb2NhbGhvc3Q6OTAwMCJdLCJyZWFsbV9hY2Nlc3MiOnsicm9sZXMiOlsib2ZmbGluZV9hY2Nlc3MiLCJ1bWFfYXV0aG9yaXphdGlvbiIsImFwcC11c2VyIiwiZGVmYXVsdC1yb2xlcy10cmF3ZWxsIl19LCJyZXNvdXJjZV9hY2Nlc3MiOnsic29jaWFsLW9hdXRoIjp7InJvbGVzIjpbInVzZXIiXX0sImtyYWtlbmQiOnsicm9sZXMiOlsidXNlciJdfSwicmVhY3QiOnsicm9sZXMiOlsidXNlciJdfSwiYWNjb3VudCI6eyJyb2xlcyI6WyJtYW5hZ2UtYWNjb3VudCIsIm1hbmFnZS1hY2NvdW50LWxpbmtzIiwidmlldy1wcm9maWxlIl19fSwic2NvcGUiOiJvcGVuaWQgcHJvZmlsZSBlbWFpbCIsInNpZCI6IjFiMDA0MmFkLWUwMDEtNDcyMC05YWFjLTYyYzUyYTg0ODU4YSIsImVtYWlsX3ZlcmlmaWVkIjp0cnVlLCJ1c2VyX3R5cGUiOiJDb21wYW55IEFjY291bnQiLCJkYXRlX29mX2JpcnRoIjoiMjAwMC0wNy0wOSIsImZhY2Vib29rIjoiIiwibmFtZSI6IkhhbGluYSBLYWN6bWFyZWsiLCJwcmVmZXJyZWRfdXNlcm5hbWUiOiJmbWFqcm94QGdtYWlsLmNvbSIsImluc3RhZ3JhbSI6IiIsImdpdmVuX25hbWUiOiJIYWxpbmEiLCJmYW1pbHlfbmFtZSI6IkthY3ptYXJlayIsImVtYWlsIjoiZm1hanJveEBnbWFpbC5jb20ifQ.LF8mzghB_oh0mlF0avL_rUKRZb1nT2pDmbhfAOTlTba3N9F1jjX_rjAL4bQ-YZlf3pw9VcD-C3GT7Mfb3HS_75CkJhkzJmJliOLQf36wOULL8j1x4iBMjcKN_Pn8Pu_u5GnEgcldeg_uuTakGN2VXgPdMuW4RkIanhqSpIQVkw8JHkNWM3q13CZ5TelTkLyHdPDaAm2xqMG-u0LFhTTUtPcep6eZ-Nk4s0YfbHyt8zW176MQmipaFV4lhzEGdWstnPqXu1oZ8X7b2v4jjoXDNeCgaYpvjOFQ-feJoGdR-jTvSWCugbSg-RDST6XL1B4vK_HMMJQAbW-C5tJHHd3omQ"


def prepare_data_for_post(additional_data={}, user_private: bool = True) -> dict:
    cities = CityFactory.create_batch(size=2)
    vehicle = VehicleFactory(**{'user__email': 'fmajrox@gmail.com', 'user__private': user_private})
    hours, minutes = 2, 30
    init_values = {'city_from': cities[0], 'city_to': cities[1], 'vehicle': vehicle,
                   'duration': datetime.timedelta(hours=hours, minutes=minutes)}
    post_data = factory.build(dict, FACTORY_CLASS=RecurrentRideFactory, **init_values)
    post_data.pop('driver')
    post_data.update({'city_from': convert_city_to_dict(init_values['city_from']),
                      'city_to': convert_city_to_dict(init_values['city_to']),
                      'duration': {'hours': hours, 'minutes': minutes}, 'vehicle': vehicle.vehicle_id,
                      'coordinates': []})
    post_data.update(additional_data)
    return post_data


class RecurrentRideViewSetTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=AUTH_TOKEN)

    def test_returns_details_for_not_authorized_user(self):
        self.client.credentials()
        ride_factory = RecurrentRideFactory()

        response = self.client.get(f"/recurrent_rides/{ride_factory.ride_id}/")
        results = response.data

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(results['ride_id'], ride_factory.ride_id)

    def test_returns_details_for_authorized_user(self):
        ride_factory = RecurrentRideFactory()

        response = self.client.get(f"/recurrent_rides/{ride_factory.ride_id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data

        self.assertEqual(results['ride_id'], ride_factory.ride_id)

    def test_get_not_existing_ride(self):
        response = self.client.get(f"/recurrent_rides/1/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_post_recurrent_ride_for_not_authorized_user(self):
        self.client.credentials()
        post_data = prepare_data_for_post()

        response = self.client.post(f"/recurrent_rides/", data=post_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_post_ride_successful(self):
        post_data = prepare_data_for_post()

        response = self.client.post(f"/recurrent_rides/", data=post_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_post_ride_missing_parameters(self):
        post_data = prepare_data_for_post()
        post_data.pop('city_from')

        response = self.client.post(f"/recurrent_rides/", data=post_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(json.loads(response.content), {'city_from': ['This field is required.']})

    def test_post_ride_creates_new_ride_and_cities(self):
        singular_rides_before_post = len(Ride.objects.all())
        recurrent_rides_before_post = len(RecurrentRide.objects.all())
        cities_before_post = len(City.objects.all())
        self.assertEqual(singular_rides_before_post, 0)
        self.assertEqual(recurrent_rides_before_post, 0)
        self.assertEqual(cities_before_post, 0)

        today = datetime.datetime.now()
        frequency_data = {'start_date': today, 'end_date': today + datetime.timedelta(days=3),
                          'frequency_type': 'daily', 'frequence': 1, 'occurrences': []}
        post_data = prepare_data_for_post(additional_data=frequency_data)

        response = self.client.post(f"/recurrent_rides/", data=post_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        singular_rides_after_post = len(Ride.objects.all())
        recurrent_rides_after_post = len(RecurrentRide.objects.all())
        cities_after_post = len(City.objects.all())
        self.assertEqual(singular_rides_after_post, 4)
        self.assertEqual(recurrent_rides_after_post, 1)
        self.assertEqual(cities_after_post, 2)

    def test_post_ride_company_user(self):
        post_data = prepare_data_for_post(user_private=False)

        response = self.client.post(f"/recurrent_rides/", data=post_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_ride_successful(self):
        user = UserFactory(email='fmajrox@gmail.com', private=True)
        vehicle = VehicleFactory.create_batch(size=2, user=user)
        ride = RecurrentRideFactory.create(seats=10, vehicle=vehicle[0], driver=user)
        patch_data = {'seats': 5, 'vehicle': vehicle[1].vehicle_id, 'description': 'updated description'}

        response = self.client.patch(f"/recurrent_rides/{ride.ride_id}/", data=patch_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        ride_obj = RecurrentRide.objects.get(ride_id=ride.ride_id)

        self.assertEqual(ride_obj.seats, patch_data['seats'])
        self.assertEqual(ride_obj.description, patch_data['description'])
        self.assertEqual(ride_obj.vehicle.vehicle_id, patch_data['vehicle'])

    def test_update_ride_company_user_successful(self):
        user = UserFactory(email='fmajrox@gmail.com', private=False)
        ride = RecurrentRideFactory.create(seats=10, driver=user, automatic_confirm=True)
        patch_data = {'seats': 5, 'automatic_confirm': False, 'description': 'updated description'}

        response = self.client.patch(f"/recurrent_rides/{ride.ride_id}/", data=patch_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        ride_obj = RecurrentRide.objects.get(ride_id=ride.ride_id)

        self.assertEqual(ride_obj.seats, patch_data['seats'])
        self.assertEqual(ride_obj.description, patch_data['description'])
        self.assertEqual(ride_obj.automatic_confirm, patch_data['automatic_confirm'])

        singular_rides = Ride.objects.filter(recurrent_ride=ride_obj).all()
        for singular_ride in singular_rides:
            self.assertEqual(singular_ride.seats, patch_data['seats'])
            self.assertEqual(singular_ride.description, patch_data['description'])
            self.assertEqual(singular_ride.automatic_confirm, patch_data['automatic_confirm'])

    def test_patch_do_not_allow_incorrect_seats(self):
        user = UserFactory(email='fmajrox@gmail.com', private=True)
        vehicle = VehicleFactory.create_batch(size=2, user=user)
        today = datetime.datetime.now()
        ride = RecurrentRideFactory.create(seats=10, vehicle=vehicle[0], driver=user, start_date=today,
                                           end_date=today + datetime.timedelta(days=10), frequency_type='daily')
        singular_ride = Ride.objects.filter(recurrent_ride__ride_id=ride.ride_id).first()

        ParticipationFactory.create(ride=singular_ride, reserved_seats=ride.seats - 1, decision='accepted')
        patch_data = {'seats': 1, 'vehicle': vehicle[1].vehicle_id, 'description': 'updated description'}

        response = self.client.patch(f"/recurrent_rides/{ride.ride_id}/", data=patch_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(json.loads(response.content), "Invalid seats parameter")

    def test_delete_ride_successfully(self):
        vehicle = VehicleFactory.create(user__email='fmajrox@gmail.com')
        ride = RecurrentRideFactory.create(seats=2, vehicle=vehicle, driver=vehicle.user)

        response = self.client.delete(f"/recurrent_rides/{ride.ride_id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        ride_obj = RecurrentRide.objects.get(ride_id=ride.ride_id)
        self.assertEqual(ride_obj.is_cancelled, True)

        singular_rides = Ride.objects.filter(recurrent_ride=ride_obj).all()
        for singular_ride in singular_rides:
            self.assertEqual(singular_ride.is_cancelled, True)

    def test_delete_ride_not_allowed(self):
        UserFactory.create(email='fmajrox@gmail.com')
        ride = RecurrentRideFactory.create()

        response = self.client.delete(f"/recurrent_rides/{ride.ride_id}/")

        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(json.loads(response.content), "User not allowed to delete ride")

    def test_recurrent_ride_produces_singular_rides(self):
        user = UserFactory(email='fmajrox@gmail.com', private=True)
        vehicle = VehicleFactory.create_batch(size=2, user=user)
        today = datetime.datetime.now()
        ride = RecurrentRideFactory.create(seats=5, vehicle=vehicle[0], driver=user, start_date=today,
                                           end_date=today + datetime.timedelta(days=6), frequency_type='weekly',
                                           occurrences=['mon', 'tue'], frequence=1)

        singular_rides = Ride.objects.filter(recurrent_ride=ride).all()
        self.assertEqual(len(singular_rides), 2)

    def _get_user_rides_response(self, user_type: str) -> (status, dict):
        RecurrentRideFactory.create_batch(size=8)

        response = self.client.get(f'/recurrent_rides/user_rides/', {'user_type': user_type})
        content = json.loads(response.content)
        return response.status_code, content

    def test_get_user_rides_as_driver_correctly(self):
        user = UserFactory.create(email='fmajrox@gmail.com')
        RecurrentRideFactory.create_batch(size=5, **{'driver': user})

        status_code, content = self._get_user_rides_response('driver')

        self.assertEqual(status_code, status.HTTP_200_OK)
        self.assertEqual(content['count'], 5)

    def test_get_single_rides(self):
        user = UserFactory.create(email='fmajrox@gmail.com')
        ride = RecurrentRideFactory.create(**{'driver': user})

        user_singular_rides = Ride.objects.filter(recurrent_ride=ride)

        response = self.client.get(f'/recurrent_rides/{ride.ride_id}/single_rides/')
        content = json.loads(response.content)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(content), len(user_singular_rides))
