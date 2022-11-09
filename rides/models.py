from datetime import timedelta

from django.contrib import admin
from django.db import models

from cities.models import City
from users.models import User
from vehicles.models import Vehicle

from django.db.models.signals import m2m_changed


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
    recurrent_ride = models.ForeignKey('recurrent_rides.RecurrentRide', related_name='single_rides',
                                       on_delete=models.CASCADE,
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
