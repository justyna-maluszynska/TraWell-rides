import datetime
import json

from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from rides.factories import RideFactory, ParticipationFactory
from rides.models import Participation
from users.factories import UserFactory

AUTH_TOKEN = "Bearer eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICJleUhzZzNlRkdiQzdTWjRQOEtWYXQ2aWJDLVlJWmE2dU03RnYycTdWQWhvIn0.eyJleHAiOjE2NjgxOTA2NDEsImlhdCI6MTY2ODE3MjY0MSwiYXV0aF90aW1lIjoxNjY4MTcyNjQxLCJqdGkiOiJhZWZlZWUwYi1iZmE3LTRlMzUtYjNmMy02NTgxYzJjZGI1MTUiLCJpc3MiOiJodHRwOi8vbG9jYWxob3N0Ojg0MDMvYXV0aC9yZWFsbXMvVHJhV2VsbCIsImF1ZCI6WyJzb2NpYWwtb2F1dGgiLCJyZWFjdCIsImFjY291bnQiXSwic3ViIjoiZmMwZjRlZTAtNzAzYS00ZTkwLWEwZTQtODdjMzIzMjkyNTk5IiwidHlwIjoiQmVhcmVyIiwiYXpwIjoia3Jha2VuZCIsInNlc3Npb25fc3RhdGUiOiIwYjBmYjVkMy05MGMyLTQ3MjEtODRkNy1iYTAxY2RkODVjZTMiLCJhY3IiOiIxIiwiYWxsb3dlZC1vcmlnaW5zIjpbImh0dHA6Ly9sb2NhbGhvc3Q6OTAwMCJdLCJyZWFsbV9hY2Nlc3MiOnsicm9sZXMiOlsib2ZmbGluZV9hY2Nlc3MiLCJ1bWFfYXV0aG9yaXphdGlvbiIsImFwcC11c2VyIiwicHJpdmF0ZV91c2VyIiwiZGVmYXVsdC1yb2xlcy10cmF3ZWxsIl19LCJyZXNvdXJjZV9hY2Nlc3MiOnsic29jaWFsLW9hdXRoIjp7InJvbGVzIjpbInVzZXIiXX0sImtyYWtlbmQiOnsicm9sZXMiOlsidXNlciJdfSwicmVhY3QiOnsicm9sZXMiOlsidXNlciJdfSwiYWNjb3VudCI6eyJyb2xlcyI6WyJtYW5hZ2UtYWNjb3VudCIsIm1hbmFnZS1hY2NvdW50LWxpbmtzIiwidmlldy1wcm9maWxlIl19fSwic2NvcGUiOiJvcGVuaWQgcHJvZmlsZSBlbWFpbCIsInNpZCI6IjBiMGZiNWQzLTkwYzItNDcyMS04NGQ3LWJhMDFjZGQ4NWNlMyIsImVtYWlsX3ZlcmlmaWVkIjp0cnVlLCJ1c2VyX3R5cGUiOiJQcml2YXRlIEFjY291bnQiLCJkYXRlX29mX2JpcnRoIjoiMjAyMi0xMC0zMSIsImZhY2Vib29rIjoiIiwibmFtZSI6Imp1c3R5bmEgbWFsIiwicHJlZmVycmVkX3VzZXJuYW1lIjoiZm1hanJveEBnbWFpbC5jb20iLCJpbnN0YWdyYW0iOiIiLCJnaXZlbl9uYW1lIjoianVzdHluYSIsImZhbWlseV9uYW1lIjoibWFsIiwiZW1haWwiOiJmbWFqcm94QGdtYWlsLmNvbSJ9.Cn_wCIPiJEgBpCBypyba0-coBKP6QEROoCE1uRuOlZNcNO5DwzIHL5QX77Zdb2CTXVjjRM3OYRFZOKtEu0zmt5UzcaUR9z88wSuW39edM7_lpZ7S1EIB0G2T0K4zNPQjgQTJshJEOMCRtjIjtFBCumntp-3RhYGdRYEh316G-8oeNoQJwZhJ4ynLnBUelpvoVVRBEGK1UICm7ylz1BkMefe_W3mlv7vMJSbqdOg4HcCQUDDnDgNLeqfcAvfveF8vuJBH7xh5L3l7mgM9ER54hgwJjcXUMHG7xGag5_yDyCstZKwtdc5qfKxTEdM3VObtprKLHU9eSJBaTlexGZoLfw"


class RequestViewSetTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=AUTH_TOKEN)

        self.user = UserFactory(email='fmajrox@gmail.com', private=True)
        self.user_rides = RideFactory.create_batch(5, driver=self.user)
        self.rides = RideFactory.create_batch(10)

    def test_sends_new_request(self):
        ride = self.rides[0]
        request_data = {'seats': ride.available_seats - 1, 'ride': ride.ride_id}

        response = self.client.post(f'/requests/', data=request_data, format='json')
        content = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(content, 'Request successfully sent')

    def test_requires_data_about_request(self):
        ride = self.rides[1]
        request_data = {'ride': ride.ride_id}

        response = self.client.post(f'/requests/', data=request_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_not_enough_seats_for_request(self):
        ride = self.rides[2]
        request_data = {'seats': ride.available_seats + 1, 'ride': ride.ride_id}

        response = self.client.post(f'/requests/', data=request_data, format='json')
        content = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(content, "There are not enough seats")

    def test_cannot_send_request_to_own_ride(self):
        ride = self.user_rides[0]
        request_data = {'seats': ride.available_seats - 1, 'ride': ride.ride_id}

        response = self.client.post(f'/requests/', data=request_data, format='json')
        content = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(content, "Driver cannot send request to join his ride")

    def test_cannot_send_requests_twice(self):
        ride = self.rides[3]

        request_data = {'seats': ride.available_seats - 1, 'ride': ride.ride_id}

        response = self.client.post(f'/requests/', data=request_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.post(f'/requests/', data=request_data, format='json')
        content = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(content, "User is already in ride or waiting for decision")

    def test_cannot_send_request_to_past_ride(self):
        ride = self.rides[4]
        ride.start_date = datetime.datetime.now()
        ride.save()
        request_data = {'seats': ride.available_seats - 1, 'ride': ride.ride_id}

        response = self.client.post(f'/requests/', data=request_data, format='json')
        content = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(content, "Ride already started or is finished")

    def test_cannot_send_request_to_not_exisiting_ride(self):
        request_data = {'seats': 10, 'ride': 100}

        response = self.client.post(f'/requests/', data=request_data, format='json')
        content = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(content, "Ride 100 not found")

    def _create_request(self):
        participation = ParticipationFactory(user=self.user)
        return participation

    def test_cancel_request_correctly(self):
        participation = self._create_request()

        response = self.client.delete(f'/requests/{participation.id}/', format='json')
        content = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(content, 'Request successfully cancelled')

        participation_obj = Participation.objects.get(id=participation.id)
        self.assertEqual(participation_obj.decision, 'cancelled')

    def test_cannot_cancel_someone_request(self):
        participation = ParticipationFactory(decision='pending')

        response = self.client.delete(f'/requests/{participation.id}/', format='json')
        content = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(content, 'User not allowed to delete request')

    def test_cannot_cancel_twice(self):
        participation = self._create_request()

        response = self.client.delete(f'/requests/{participation.id}/', format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.delete(f'/requests/{participation.id}/', format='json')
        content = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(content, 'Request is already cancelled')
