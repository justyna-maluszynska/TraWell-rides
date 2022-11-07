from __future__ import absolute_import, unicode_literals

from celery import shared_task

from rides_microservice.celery import app, queue_notify


@shared_task(name='notification')
def publish_message(message, title):
    body = {
        'title': title,
        'message': message
    }
    with app.producer_pool.acquire(block=True) as producer:
        producer.publish(
            body,
            exchange='trawell_exchange',
            queue=queue_notify,
            routing_key='notify',
        )
