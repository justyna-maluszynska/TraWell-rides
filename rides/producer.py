import django
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rides_microservice.settings")
django.setup()

import json
import pika

parameters = pika.ConnectionParameters(host='host.docker.internal', port=5672)
connection = pika.BlockingConnection(parameters)

channel = connection.channel()

channel.queue_declare(queue='rides')


def publish(method, body):
    properties = pika.BasicProperties(method)
    channel.basic_publish(exchange='', routing_key='rides', body=json.dumps(body), properties=properties)
    print('send message')



# def publish(method, body):
#     pass
