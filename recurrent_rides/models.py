from datetime import timedelta

import pandas as pd
from django.contrib.postgres.fields import ArrayField
from django.db import models
from pandas import DatetimeIndex

from cities.models import City
from rides.services import create_ride
from rides.utils.constants import ACTUAL_RIDES_ARGS
from users.models import User
from vehicles.models import Vehicle


class RecurrentRide(models.Model):
    class FrequencyType(models.TextChoices):
        HOURLY = 'hourly'
        DAILY = 'daily'
        WEEKLY = 'weekly'
        MONTHLY = 'monthly'

    class WeekDays(models.TextChoices):
        MONDAY = 'MON'
        TUESDAY = 'TUE'
        WEDNESDAY = 'WED'
        THURSDAY = 'THU'
        FRIDAY = 'FRI'
        SATURDAY = 'SAT'
        SUNDAY = 'SUN'

    ride_id = models.AutoField(primary_key=True)
    city_from = models.ForeignKey(City, related_name='recur_city_from', blank=False, null=True,
                                  on_delete=models.SET_NULL)
    city_to = models.ForeignKey(City, related_name='recur_city_to', blank=False, null=True, on_delete=models.SET_NULL)
    area_from = models.CharField(max_length=100, blank=True, default="")
    area_to = models.CharField(max_length=100, blank=True, default="")
    start_date = models.DateTimeField(null=False)
    end_date = models.DateTimeField(null=False)
    frequency_type = models.CharField(choices=FrequencyType.choices, default=FrequencyType.DAILY, max_length=9)
    frequence = models.IntegerField(default=1, blank=False, null=False)
    occurrences = ArrayField(models.CharField(max_length=10, choices=WeekDays.choices), blank=True, null=True)
    duration = models.DurationField(blank=False, default=timedelta)
    price = models.DecimalField(null=False, max_digits=10, decimal_places=2)
    seats = models.PositiveIntegerField(null=False)
    automatic_confirm = models.BooleanField(null=False, default=False)
    description = models.TextField(blank=True, default="")
    driver = models.ForeignKey(User, on_delete=models.SET_NULL, blank=False, null=True)
    vehicle = models.ForeignKey(Vehicle, on_delete=models.SET_NULL, blank=False, null=True)
    is_cancelled = models.BooleanField(default=False, blank=False)

    def save(self, *args, **kwargs):
        if not self.ride_id:
            super(RecurrentRide, self).save(*args, **kwargs)

        create_or_update_single_rides(self)
        super(RecurrentRide, self).save()


def create_or_update_single_rides(recurrent_ride: RecurrentRide) -> None:
    frequency_type = recurrent_ride.frequency_type
    start_date = recurrent_ride.start_date
    end_date = recurrent_ride.end_date
    frequence = recurrent_ride.frequence
    occurrences = recurrent_ride.occurrences

    if frequency_type in RecurrentRide.FrequencyType.HOURLY:
        dates = pd.date_range(start=start_date, end=end_date, freq=f'{frequence}H')
    elif frequency_type in RecurrentRide.FrequencyType.DAILY:
        dates = pd.date_range(start=start_date, end=end_date, freq=f'{frequence}D')
    elif frequency_type in RecurrentRide.FrequencyType.WEEKLY:
        dates = DatetimeIndex()
        for occurrence in occurrences:
            dates.union(pd.date_range(start=start_date, end=end_date, freq=f'{frequence}W-{occurrence}'))
    elif frequency_type in RecurrentRide.FrequencyType.MONTHLY:
        dates = pd.date_range(start=start_date, end=end_date, freq=f'{frequence}M')

    data = {"driver": recurrent_ride.driver, "vehicle": recurrent_ride.vehicle,
            "city_from": recurrent_ride.city_from,
            "city_to": recurrent_ride.city_to, "duration": recurrent_ride.duration,
            "area_from": recurrent_ride.area_from, "area_to": recurrent_ride.area_to,
            "price": recurrent_ride.price, "seats": recurrent_ride.seats, "recurrent": True,
            "automatic_confirm": recurrent_ride.automatic_confirm, "description": recurrent_ride.description, }

    if recurrent_ride.single_rides.exists():
        recurrent_ride.single_rides.filter(**ACTUAL_RIDES_ARGS).update(**data)
    else:
        for start_date in dates:
            data['start_date'] = start_date
            data['recurrent_ride'] = recurrent_ride
            create_ride(data)
