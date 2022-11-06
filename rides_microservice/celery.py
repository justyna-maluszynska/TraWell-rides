from __future__ import absolute_import, unicode_literals

import os

import django
import kombu
from celery import Celery, bootsteps

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

    queue_rides = kombu.Queue(
        name='rides',
        exchange=exchange,
        routing_key='key.#',
        channel=conn,
        message_ttl=600,
        queue_arguments={
            'x-queue-type': 'classic'
        },
        durable=True
    )
    queue_rides.declare()


# setting consumer
class MyConsumerStep(bootsteps.ConsumerStep):

    def get_consumers(self, channel):
        print('get consumers')
        return [kombu.Consumer(channel,
                               queues=[queue_rides],
                               callbacks=[self.handle_message],
                               accept=['json'])]

    def handle_message(self, body, message):
        print('handle_message')
        print('Received message: {0!r}'.format(body))
        print(message)
        # message_data = json.loads(message)
        if message.delivery_info['routing_key'] == 'key.users':
            try:
                user = User.objects.get(user_id=body['user_id'])
                user_data = {'first_name': body['first_name'],
                             'last_name': body["last_name"],
                             'avatar': body['avatar']
                             }
                serializer = UserSerializer(user, data=user_data, partial=True)
                if serializer.is_valid():
                    serializer.save()
                    print('User updated!')

            except User.DoesNotExist:
                new_user = User.objects.create(first_name=body['first_name'],
                                               last_name=body["last_name"],
                                               email=body["email"],
                                               avatar=body['avatar'],
                                               private=True if body['user_type'] == 'private' else False,
                                               avg_rate=0.0,
                                               user_id=body['user_id']
                                               )
                new_user.save()
                print('New user created!')
            message.ack()

        if message.delivery_info['routing_key'] == 'key.vehicles':
            print('Message received on vehicles queue')

            try:
                User.objects.get(user_id=body['user']['user_id'])

            except User.DoesNotExist:
                new_user = User.objects.create(first_name=body['user']['first_name'],
                                               last_name=body['user']["last_name"],
                                               email=body['user']["email"],
                                               avatar=body['user']['avatar'],
                                               private=True if body['user'][
                                                                   'user_type'] == 'private' else False,
                                               avg_rate=0.0,
                                               user_id=body['user']['user_id']
                                               )
                new_user.save()
                print('New user created!')

            new_vehicle = Vehicle.objects.create(vehicle_id=body['vehicle_id'],
                                                 make=body['make'],
                                                 model=body['model'],
                                                 color=body['color'],
                                                 user_id=body['user']['user_id'])
            new_vehicle.save()
            print('New vehicle created!')
            message.ack()


app.steps['consumer'].add(MyConsumerStep)

