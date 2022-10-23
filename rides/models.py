from datetime import timedelta

from django.contrib import admin
from django.db import models

from cities.models import City
from users.models import User
from vehicles.models import Vehicle

from django.db.models.signals import m2m_changed


# Create your models here.
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

    @property
    def get_available_seats(self):
        if self.ride_id is None:
            return None

        return self.seats - len(self.passengers.filter(passenger__decision='accepted'))

    @property
    def can_driver_edit(self):
        return not self.passengers.filter(passenger__decision__in=['accepted', 'pending']).exists()

    def save(self, *args, **kwargs):
        super(Ride, self).save(*args, **kwargs)


class Participation(models.Model):
    class Decision(models.TextChoices):
        ACCEPTED = 'accepted'
        DECLINED = 'declined'
        PENDING = 'pending'
        CANCELLED = 'cancelled'

    ride = models.ForeignKey(Ride, on_delete=models.SET_NULL, null=True)
    user = models.ForeignKey(User, related_name='passenger', on_delete=models.SET_NULL, null=True)
    decision = models.CharField(choices=Decision.choices, default=Decision.PENDING, max_length=9)

    def delete(self, using=None, keep_parents=False):
        super(Participation, self).delete(using, keep_parents)
        self.ride.available_seats = self.ride.get_available_seats
        self.ride.save()

    def save(self, *args, **kwargs):
        super(Participation, self).save(*args, **kwargs)
        self.ride.available_seats = self.ride.get_available_seats
        self.ride.save()


def participation_changed(sender, instance, action, **kwargs):
    if action in 'post_add':
        instance.available_seats = instance.get_available_seats
        instance.save()


m2m_changed.connect(participation_changed, sender=Ride.passengers.through)


class Coordinate(models.Model):
    coordinate_id = models.AutoField(primary_key=True)
    ride = models.ForeignKey(Ride, related_name='coordinates', on_delete=models.CASCADE, null=False)
    lat = models.DecimalField(null=False, max_digits=15, decimal_places=6)
    lng = models.DecimalField(null=False, max_digits=15, decimal_places=6)
    sequence_no = models.IntegerField(null=False)


class ParticipationInline(admin.TabularInline):
    model = Participation


class RideAdmin(admin.ModelAdmin):
    inlines = (ParticipationInline,)
