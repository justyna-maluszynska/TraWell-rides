import datetime

import scripts.create_cities
from cities.models import City
from recurrent_rides.models import RecurrentRide
from rides.models import Ride, Participation
from rides.serializers import RideSerializer, ParticipationSerializer
from rides_microservice import tasks
from rides_microservice.celery import queue_notify, queue_reviews
from users.models import User
from vehicles.models import Vehicle

rides = [
    {'city_from': 5,  # id of city from db
     'city_to': 1,  # id of city from db
     'area_from': 'fromfromfrom',
     'area_to': 'totototo',
     'start_date': datetime.datetime(2022, 12, 20, 20),
     'duration': datetime.timedelta(seconds=3600),
     'price': 20.50,
     'seats': 3,
     'recurrent': False,
     'automatic_confirm': False,
     'description': 'lalala',
     'driver_email': 'anna@sowa.com',
     'is_cancelled': False,
     'recurrent_ride': None}
]

participations = [
    {'ride_id': 1,
     'user_email': 'jan@kot.com',
     'decision': 'accepted',
     'reserved_seats': 2}
]

recurrent_rides = [
    {'city_from': 5,  # id of city from db
     'city_to': 1,  # id of city from db
     'area_from': 'park',
     'area_to': 'bar',
     'start_date': datetime.datetime(2022, 11, 1, 18),
     'end_date': datetime.datetime(2023, 1, 10, 19),
     'frequency_type': 'daily',
     'frequence': 1,
     'occurrences': None,
     'duration': datetime.timedelta(seconds=2100),
     'price': 26.99,
     'seats': 6,
     'automatic_confirm': False,
     'description': 'Best ride ever',
     'driver_email': 'anna@sowa.com',
     'is_cancelled': False},
    {'city_from': 5,  # id of city from db
     'city_to': 1,  # id of city from db
     'area_from': 'ul. Warszawska',
     'area_to': 'dom kultury',
     'start_date': datetime.datetime(2022, 11, 26, 16),
     'end_date': datetime.datetime(2023, 2, 1, 20),
     'frequency_type': 'daily',
     'frequence': 1,
     'occurrences': None,
     'duration': datetime.timedelta(seconds=5000),
     'price': 5.99,
     'seats': 5,
     'automatic_confirm': True,
     'description': 'Super rides for everyone',
     'driver_email': 'jan@kot.com',
     'is_cancelled': False},
    {'city_from': 2,  # id of city from db
     'city_to': 3,  # id of city from db
     'area_from': 'ul. Mazowiecka 55a',
     'area_to': 'przystanek na Wesołej',
     'start_date': datetime.datetime(2022, 11, 1, 14),
     'end_date': datetime.datetime(2023, 1, 24, 14),
     'frequency_type': 'daily',
     'frequence': 1,
     'occurrences': None,
     'duration': datetime.timedelta(seconds=800),
     'price': 67.32,
     'seats': 5,
     'automatic_confirm': False,
     'description': '<3',
     'driver_email': 'anna@sowa.com',
     'is_cancelled': False}
]


def create_manual_rides(rides):
    for ride in rides:
        city_from = City.objects.get(city_id=ride['city_from'])
        city_to = City.objects.get(city_id=ride['city_to'])
        driver = User.objects.get(email=ride['driver_email'])
        vehicles = Vehicle.objects.filter(user=driver)
        if len(vehicles) > 0:
            vehicle = vehicles[0]
        else:
            vehicle = None
        new_ride = Ride.objects.create(city_from=city_from,
                                       city_to=city_to,
                                       area_from=ride['area_from'],
                                       area_to=ride['area_to'],
                                       start_date=ride['start_date'],
                                       duration=ride['duration'],
                                       price=ride['price'],
                                       seats=ride['seats'],
                                       recurrent=ride['recurrent'],
                                       automatic_confirm=ride['automatic_confirm'],
                                       description=ride['description'],
                                       driver=driver,
                                       vehicle=vehicle,
                                       is_cancelled=ride['is_cancelled'],
                                       recurrent_ride=ride['recurrent_ride'])
        new_ride.save()

        serializer = RideSerializer(new_ride)
        tasks.publish_message(serializer.data, 'rides.create', queue_notify, 'notify')
        tasks.publish_message(serializer.data, 'rides.create', queue_reviews, 'review')


def create_manual_participations(participations):
    for participation in participations:
        ride = Ride.objects.get(ride_id=participation['ride_id'])
        user = User.objects.get(email=participation['user_email'])
        new_participation = Participation.objects.create(ride=ride,
                                                         user=user,
                                                         decision=participation['decision'],
                                                         reserved_seats=participation['reserved_seats'])

        tasks.publish_message(ParticipationSerializer(new_participation).data, 'participation', queue_notify, 'notify')
        tasks.publish_message(ParticipationSerializer(new_participation).data, 'participation', queue_reviews, 'review')


def create_manual_recurrent_rides(recurrent_rides):
    for ride in recurrent_rides:
        city_from = City.objects.get(city_id=ride['city_from'])
        city_to = City.objects.get(city_id=ride['city_to'])
        driver = User.objects.get(email=ride['driver_email'])
        vehicles = Vehicle.objects.filter(user=driver)
        if len(vehicles) > 0:
            vehicle = vehicles[0]
        else:
            vehicle = None
        new_ride = RecurrentRide.objects.create(city_from=city_from,
                                                city_to=city_to,
                                                area_from=ride['area_from'],
                                                area_to=ride['area_to'],
                                                start_date=ride['start_date'],
                                                end_date=ride['end_date'],
                                                frequency_type=ride['frequency_type'],
                                                frequence=ride['frequence'],
                                                occurrences=ride['occurrences'],
                                                duration=ride['duration'],
                                                price=ride['price'],
                                                seats=ride['seats'],
                                                automatic_confirm=ride['automatic_confirm'],
                                                description=ride['description'],
                                                driver=driver,
                                                vehicle=vehicle,
                                                is_cancelled=ride['is_cancelled'])
        new_ride.save()

        rides = Ride.objects.filter(recurrent_ride=new_ride).all()
        serializer = RideSerializer(instance=rides, many=True)
        tasks.publish_message(serializer.data, 'rides.create.many', queue_notify, 'notify')
        tasks.publish_message(serializer.data, 'rides.create.many', queue_reviews, 'review')


scripts.create_cities.create()
create_manual_rides(rides)
create_manual_participations(participations)
create_manual_recurrent_rides(recurrent_rides)
