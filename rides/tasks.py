from __future__ import absolute_import, unicode_literals

from celery import shared_task

from rides_microservice.celery import app


@shared_task
def publish_message(message):
    with app.producer_pool.acquire(block=True) as producer:
        producer.publish(
            message,
            exchange='trawell_exchange',
            routing_key='notify.rides',
        )
