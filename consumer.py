
import django
import json
import os
import pika

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rides_microservice.settings")
django.setup()

from vehicles.models import Vehicle

params = pika.URLParameters('amqp://admin:password@localhost:5672')

connection = pika.BlockingConnection(params)

channel = connection.channel()

channel.queue_declare(queue='vehicles')


def callback(ch, method, properties, body):
    print('Received in admin')
    id = json.loads(body)
    print(id)

    product = Vehicle.objects.get(id=id)
    product.likes = product.likes + 1
    product.save()
    print('Product likes increased!')


channel.basic_consume(queue='vehicles', on_message_callback=callback, auto_ack=True)

print('Started Consuming')

channel.start_consuming()

channel.close()
