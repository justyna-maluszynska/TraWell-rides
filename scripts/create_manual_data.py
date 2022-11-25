from datetime import datetime

from cities.models import City
from recurrent_rides.models import RecurrentRide
from rides.models import Ride, Participation
from rides.serializers import RideSerializer, ParticipationSerializer
from rides_microservice import tasks
from rides_microservice.celery import queue_notify, queue_reviews
from users.models import User
from vehicles.models import Vehicle

rides = [
    {'city_from': 1,    # id of city from db
     'city_to': 2,  # id of city from db
     'area_from': 'fromfromfrom',
     'area_to': 'totototo',
     'start_date': datetime(2022, 12, 20, 9),
     'duration': datetime.timedelta(seconds = 3600),
     'price': 20.50,
     'seats': 3,
     'recurrent': False,
     'automatic_confirm': False,
     'description': 'lalala',
     'driver_email': 'anna.nowak@wp.pl',
     'vehicle_id': 1,   #make sure that the vehicle belongs to driver
     'is_cancelled': False,
     'recurrent_ride': None}
]


participations = [
    {'ride_id': 1,
     'user_email': 'newmail@gmail.com',
     'decision': 'accepted',
     'reserved_seats': 2}
]


recurrent_rides = [
    {'city_from': 1,    # id of city from db
     'city_to': 2,  # id of city from db
     'area_from': 'fromfromfrom',
     'area_to': 'totototo',
     'start_date': datetime(2022, 12, 1, 9),
     'end_date': datetime(2023, 1, 30, 9),
     'frequency_type': 'weekly',
     'frequence': 1,
     'occurences': None,
     'duration': datetime.timedelta(seconds=3600),
     'price': 20.50,
     'seats': 3,
     'automatic_confirm': False,
     'description': 'lalala',
     'driver_email': 'anna.nowak@wp.pl',
     'vehicle_id': 1,   #make sure that the vehicle belongs to driver
     'is_cancelled': False}
]


def create_manual_rides(rides):
    for ride in rides:
        city_from = City.objects.get(city_id=ride['city_from'])
        city_to = City.objects.get(city_id=ride['city_to'])
        driver = User.objects.get(email=ride['email'])
        vehicle = Vehicle.objects.get(vehicle_id=ride['vehicle_id'])
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

        serializer = RideSerializer(ride)
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
        driver = User.objects.get(email=ride['email'])
        vehicle = Vehicle.objects.get(vehicle_id=ride['vehicle_id'])
        new_ride = RecurrentRide.objects.create(city_from=city_from,
                                                city_to=city_to,
                                                area_from=ride['area_from'],
                                                area_to=ride['area_to'],
                                                start_date=ride['start_date'],
                                                end_date=ride['end_date'],
                                                frequency_type=ride['frequency_type'],
                                                frequence=ride['frequence'],
                                                occurences=ride['occurences'],
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
