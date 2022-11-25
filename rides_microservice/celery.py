from __future__ import absolute_import, unicode_literals

import os

import django
import kombu
from celery import Celery, bootsteps
from kombu import Queue

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rides_microservice.settings')
django.setup()

from users.models import User
from users.serializers import UserSerializer
from vehicles.models import Vehicle

app = Celery('rides_microservice')

app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# setting publisher
with app.pool.acquire(block=True) as conn:
    exchange = kombu.Exchange(
        name='trawell_exchange',
        type='direct',
        durable=True,
        channel=conn,
    )
    exchange.declare()

    queue_notify = kombu.Queue(
        name='notifications',
        exchange=exchange,
        routing_key='notify',
        channel=conn,
        message_ttl=600,
        queue_arguments={
            'x-queue_rides-type': 'classic'
        },
        durable=True
    )
    queue_notify.declare()

    queue_reviews = kombu.Queue(
        name='reviews',
        exchange=exchange,
        routing_key='review',
        channel=conn,
        message_ttl=600,
        queue_arguments={
            'x-queue_rides-type': 'classic'
        },
        durable=True
    )
    queue_reviews.declare()

    queue_rides = kombu.Queue(
        name='rides',
        exchange=exchange,
        routing_key='send',
        channel=conn,
        message_ttl=600,
        queue_arguments={
            'x-queue_rides-type': 'classic'
        },
        durable=True
    )
    queue_rides.declare()


# setting consumer
class MyConsumerStep(bootsteps.ConsumerStep):

    def get_consumers(self, channel):
        return [kombu.Consumer(channel,
                               queues=[queue_rides],
                               callbacks=[self.handle_message],
                               accept=['json'])]

    def handle_message(self, body, message):
        print('Received message: {0!r}'.format(body))
        print(message)
        if body['title'] == 'users':
            try:
                user = User.objects.get(user_id=body['message']['user_id'])
                user_data = {
                    'first_name': body['message']['first_name'],
                    'last_name': body['message']["last_name"],
                    'avatar': body['message']['avatar'],
                    'avg_rate': body['message']['avg_rate']
                }
                serializer = UserSerializer(user, data=user_data, partial=True)
                if serializer.is_valid():
                    serializer.save()

            except User.DoesNotExist:
                new_user = User.objects.create(
                    user_id=body['message']['user_id'],
                    first_name=body['message']['first_name'],
                    last_name=body['message']["last_name"],
                    email=body['message']["email"],
                    avatar=body['message']['avatar'],
                    private=True if body['message']['user_type'] == 'private' else False,
                    avg_rate=body['message']['avg_rate']
                )
                new_user.save()

        if body['title'] == 'vehicles.create':
            try:
                User.objects.get(user_id=body['message']['user']['user_id'])

            except User.DoesNotExist:
                new_user = User.objects.create(
                    user_id=body['message']['user']['user_id'],
                    first_name=body['message']['user']['first_name'],
                    last_name=body['message']['user']["last_name"],
                    email=body['message']['user']["email"],
                    avatar=body['message']['user']['avatar'],
                    private=True if body['message']['user']['user_type'] == 'private' else False,
                    avg_rate=body['message']['user']['avg_rate']
                )
                new_user.save()

            try:
                Vehicle.objects.get(vehicle_id=body['message']['vehicle_id'])
            except Vehicle.DoesNotExist:
                new_vehicle = Vehicle.objects.create(
                    vehicle_id=body['message']['vehicle_id'],
                    make=body['message']['make'],
                    model=body['message']['model'],
                    color=body['message']['color'],
                    user_id=body['message']['user']['user_id']
                )
                new_vehicle.save()

        if body['title'] == 'vehicles.patch':
            print('Message received on vehicles queue_rides\n patch proly should not be implemented')

        if body['title'] == 'vehicles.delete':
            try:
                vehicle = Vehicle.objects.get(vehicle_id=body['message']['vehicle_id'])
                vehicle.delete()
            except Vehicle.DoesNotExist:
                pass

        message.ack()


app.steps['consumer'].add(MyConsumerStep)
