import json
import logging
import os

import pika
from sys import path
from os import environ

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rides_microservice.settings')
import django

django.setup()

from users.models import User
from users.serializers import UserSerializer
from vehicles.models import Vehicle

path.append('/TraWell-rides/rides_microservice/settings.py')
environ.setdefault('DJANGO_SETTINGS_MODULE', 'rides_microservice.settings')
django.setup()

logger = logging.getLogger(__name__)

# credentials = pika.PlainCredentials('admin', 'password')
parameters = pika.ConnectionParameters(host='host.docker.internal', port=5672, virtual_host='/')
connection = pika.BlockingConnection(parameters)

channel = connection.channel()

channel.queue_declare(queue='users')
channel.queue_declare(queue='vehicles')


def callback_users(ch, method, properties, body):
    print('Message received on users queue')
    user_data = json.loads(body)

    try:
        user = User.objects.get(user_id=user_data['user_id'])
        user_data = {'first_name': user_data['first_name'],
                     'last_name': user_data["last_name"],
                     'avatar': user_data['avatar']
                     }
        serializer = UserSerializer(user, data=user_data, partial=True)
        if serializer.is_valid():
            serializer.save()
            print('User updated!')

    except User.DoesNotExist:
        new_user = User.objects.create(first_name=user_data['first_name'],
                                       last_name=user_data["last_name"],
                                       email=user_data["email"],
                                       avatar=user_data['avatar'],
                                       private=True if user_data['user_type'] == 'private' else False,
                                       avg_rate=0.0,
                                       user_id=user_data['user_id']
                                       )
        new_user.save()
        print('New user created!')


def callback_vehicles(ch, method, properties, body):
    print('Message received on vehicles queue')
    vehicle_data = json.loads(body)

    if properties.content_type == 'vehicle_created':
        try:
            User.objects.get(user_id=vehicle_data['user']['user_id'])

        except User.DoesNotExist:
            new_user = User.objects.create(first_name=vehicle_data['user']['first_name'],
                                           last_name=vehicle_data['user']["last_name"],
                                           email=vehicle_data['user']["email"],
                                           avatar=vehicle_data['user']['avatar'],
                                           private=True if vehicle_data['user']['user_type'] == 'private' else False,
                                           avg_rate=0.0,
                                           user_id=vehicle_data['user']['user_id']
                                           )
            new_user.save()
            print('New user created!')

        new_vehicle = Vehicle.objects.create(vehicle_id=vehicle_data['vehicle_id'],
                                             make=vehicle_data['make'],
                                             model=vehicle_data['model'],
                                             color=vehicle_data['color'],
                                             user_id=vehicle_data['user']['user_id'])
        new_vehicle.save()
        print('New vehicle created!')


channel.basic_consume(queue='users', on_message_callback=callback_users, auto_ack=True)

channel.basic_consume(queue='vehicles', on_message_callback=callback_vehicles, auto_ack=True)

print('Started Consuming')
logger.debug("Started Consuming")
logger.debug("--------------------------")

channel.start_consuming()

channel.close()
