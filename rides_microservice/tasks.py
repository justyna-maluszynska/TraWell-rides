from __future__ import absolute_import, unicode_literals
import datetime

from celery import shared_task
from rides_microservice.celery import app, queue_reviews, queue_history
from rides.serializers import RideSerializer, RideForHistorySerializer, RideForReviewsSerializer
from django.db.models import Q
from rides.models import Ride


@shared_task(name='data_messaging')
def publish_message(message, title, queue, routing_key):
    body = {
        'title': title,
        'message': message
    }
    with app.producer_pool.acquire(block=True) as producer:
        producer.publish(
            body,
            exchange='trawell_exchange',
            queue=queue,
            routing_key=routing_key,
        )

@app.task(queue='archive_queue')
def archive():
    current_time = datetime.datetime.now()
    rides = Ride.objects.filter(Q(start_date__lte=current_time) | Q(is_cancelled=True), was_archived=False)
    history_serializer = RideForHistorySerializer(instance=rides, many=True)
    reviews_serializer = RideForReviewsSerializer(instance=rides, many=True)

    publish_message(reviews_serializer.data, 'rides.archive', queue_reviews, 'review')
    publish_message(history_serializer.data, 'rides.archive', queue_history, 'history')

    for ride in rides:
        ride.was_archived = True
        ride.save()


@app.task(queue='archive_queue')
def clear_from_archived():
    rides = Ride.objects.filter(was_archived=True)

    serializer = RideForHistorySerializer(instance=rides, many=True)
    publish_message(serializer.data, 'rides.sync', queue_history, 'history')

    rides.delete()
