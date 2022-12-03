from __future__ import absolute_import, unicode_literals

import os

import django
import kombu
from celery import Celery, bootsteps

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rides_microservice.settings')
django.setup()

from utils.celery_utils import create_user, create_vehicle, delete_vehicle

app = Celery('rides_microservice')

app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# setting publisher
with app.pool.acquire(block=True) as conn:
    exchange_main = kombu.Exchange(
        name='trawell_exchange',
        type='direct',
        durable=True,
        channel=conn,
    )

    exchange_main.declare()

    queue_notify = kombu.Queue(
        name='notifications',
        exchange=exchange_main,
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
        exchange=exchange_main,
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
        exchange=exchange_main,
        routing_key='send',
        channel=conn,
        message_ttl=600,
        queue_arguments={
            'x-queue_rides-type': 'classic'
        },
        durable=True
    )
    queue_rides.declare()

    queue_history = kombu.Queue(
        name='history',
        exchange=exchange_main,
        routing_key='history',
        channel=conn,
        x_message_ttl=600,
        queue_arguments={
            'x-queue_rides-type': 'classic',
            'x-message-ttl': 600000,
        },
        durable=True
    )
    queue_history.declare()


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
            create_user(body['message'])

        if body['title'] == 'vehicles.create':
            create_vehicle(body['message'])

        if body['title'] == 'vehicles.delete':
            delete_vehicle(body['message'])

        message.ack()


app.steps['consumer'].add(MyConsumerStep)
