from datetime import timedelta

import pandas as pd
from django.contrib import admin
from django.contrib.postgres.fields import ArrayField
from django.db import models
from pandas import DatetimeIndex

from cities.models import City
from users.models import User
from vehicles.models import Vehicle

from django.db.models.signals import m2m_changed


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

        create_single_rides(self)
        super(RecurrentRide, self).save(*args, **kwargs)


class Ride(models.Model):
    ride_id = models.AutoField(primary_key=True)
    city_from = models.ForeignKey(City, related_name='city_from', blank=False, null=True, on_delete=models.SET_NULL)
    city_to = models.ForeignKey(City, related_name='city_to', blank=False, null=True, on_delete=models.SET_NULL)
    area_from = models.CharField(max_length=100, blank=True, default="")
    area_to = models.CharField(max_length=100, blank=True, default="")
    start_date = models.DateTimeField(null=False)
    duration = models.DurationField(blank=False, default=timedelta)
    price = models.DecimalField(null=False, max_digits=10, decimal_places=2)
    seats = models.PositiveIntegerField(null=False)
    recurrent = models.BooleanField(null=False, default=False)
    automatic_confirm = models.BooleanField(null=False, default=False)
    description = models.TextField(blank=True, default="")
    driver = models.ForeignKey(User, related_name='driver', on_delete=models.SET_NULL, blank=False, null=True)
    vehicle = models.ForeignKey(Vehicle, related_name='ride', on_delete=models.SET_NULL, blank=False, null=True)
    passengers = models.ManyToManyField(User, blank=True, through='Participation')
    available_seats = models.IntegerField(null=True, blank=True)
    is_cancelled = models.BooleanField(default=False, blank=False)
    recurrent_ride = models.ForeignKey(RecurrentRide, related_name='single_rides', on_delete=models.CASCADE,
                                       blank=True, null=True, default=None)

    @property
    def get_available_seats(self) -> int:
        passengers = self.passengers.filter(
            passenger__decision__in=[Participation.Decision.PENDING, Participation.Decision.ACCEPTED]).all()
        reserved_seats = sum(
            passenger.passenger.filter(ride_id=self.ride_id).first().reserved_seats for passenger in passengers)

        return self.seats - reserved_seats

    @property
    def can_driver_edit(self):
        return not self.passengers.filter(passenger__decision__in=['accepted', 'pending']).exists()

    def save(self, *args, **kwargs):
        if not self.ride_id:
            super(Ride, self).save(*args, **kwargs)
        # if not self.available_seats:
        #     self.available_seats = self.get_available_seats
        self.available_seats = self.get_available_seats
        super(Ride, self).save()


class Participation(models.Model):
    class Decision(models.TextChoices):
        ACCEPTED = 'accepted'
        DECLINED = 'declined'
        PENDING = 'pending'
        CANCELLED = 'cancelled'

    ride = models.ForeignKey(Ride, on_delete=models.SET_NULL, null=True)
    user = models.ForeignKey(User, related_name='passenger', on_delete=models.SET_NULL, null=True)
    decision = models.CharField(choices=Decision.choices, default=Decision.PENDING, max_length=9)
    reserved_seats = models.IntegerField(default=1, blank=False, null=False)

    def delete(self, using=None, keep_parents=False):
        super(Participation, self).delete(using, keep_parents)
        # self.ride.available_seats = self.ride.get_available_seats
        self.ride.save()

    def save(self, *args, **kwargs):
        super(Participation, self).save(*args, **kwargs)
        # self.ride.available_seats = self.ride.get_available_seats
        self.ride.save()


def participation_changed(sender, instance, action, **kwargs):
    if action in 'post_add':
        instance.available_seats = instance.get_available_seats
        instance.save()


m2m_changed.connect(participation_changed, sender=Ride.passengers.through)


class Coordinate(models.Model):
    coordinate_id = models.AutoField(primary_key=True)
    ride = models.ForeignKey(Ride, related_name='coordinates', on_delete=models.CASCADE, null=True)
    lat = models.DecimalField(null=False, max_digits=15, decimal_places=6)
    lng = models.DecimalField(null=False, max_digits=15, decimal_places=6)
    sequence_no = models.IntegerField(null=False)


class ParticipationInline(admin.TabularInline):
    model = Participation


class RideAdmin(admin.ModelAdmin):
    inlines = (ParticipationInline,)


def create_single_rides(recurrent_ride: RecurrentRide) -> None:
    frequency_type = recurrent_ride.frequency_type
    start_date = recurrent_ride.start_date
    end_date = recurrent_ride.end_date
    frequence = recurrent_ride.frequence
    occurrences = recurrent_ride.occurrences

    if frequency_type in RecurrentRide.FrequencyType.HOURLY:
        dates = pd.date_range(start=start_date, end=end_date, freq=f'{frequence}H')
    elif frequency_type in RecurrentRide.FrequencyType.DAILY:
        print('weszlo')
        dates = pd.date_range(start=start_date, end=end_date, freq=f'{frequence}D')
    elif frequency_type in RecurrentRide.FrequencyType.WEEKLY:
        dates = DatetimeIndex()
        for occurrence in occurrences:
            dates.union(pd.date_range(start=start_date, end=end_date, freq=f'{frequence}W-{occurrence}'))
    elif frequency_type in RecurrentRide.FrequencyType.MONTHLY:
        dates = pd.date_range(start=start_date, end=end_date, freq=f'{frequence}M')

    for start_date in dates:
        ride = Ride(driver=recurrent_ride.driver, vehicle=recurrent_ride.vehicle, city_from=recurrent_ride.city_from,
                    city_to=recurrent_ride.city_to, duration=recurrent_ride.duration,
                    area_from=recurrent_ride.area_from, area_to=recurrent_ride.area_to, start_date=start_date,
                    price=recurrent_ride.price, seats=recurrent_ride.seats, recurrent=True,
                    automatic_confirm=recurrent_ride.automatic_confirm, description=recurrent_ride.description,
                    recurrent_ride=recurrent_ride)
        ride.save()
