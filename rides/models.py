from django.db import models

from cities.models import City
from users.models import User
from vehicles.models import Vehicle


# Create your models here.
class Ride(models.Model):
    ride_id = models.AutoField(primary_key=True)
    city_from = models.ForeignKey(City, related_name='city_from', blank=False, null=True, on_delete=models.SET_NULL)
    city_to = models.ForeignKey(City, related_name='city_to', blank=False, null=True, on_delete=models.SET_NULL)
    area_from = models.CharField(max_length=100)
    area_to = models.CharField(max_length=100)
    start_date = models.DateTimeField(null=False)
    end_date = models.DateTimeField(null=False)
    price = models.DecimalField(null=False, max_digits=10, decimal_places=2)
    seats = models.IntegerField(null=False)
    recurrent = models.BooleanField(null=False, default=False)
    automatic_confirm = models.BooleanField(null=False, default=False)
    description = models.TextField()
    driver = models.ForeignKey(User, related_name='driver', on_delete=models.SET_NULL, blank=False, null=True)
    vehicle = models.ForeignKey(Vehicle, related_name='ride', on_delete=models.SET_NULL, blank=False, null=True)
    passengers = models.ManyToManyField(User, related_name='passenger', blank=True)
    duration = models.DurationField(null=True, blank=True)
    available_seats = models.IntegerField(null=True, blank=True)

    @property
    def get_duration(self):
        return self.end_date - self.start_date

    @property
    def get_available_seats(self):
        return self.seats - len(self.passengers.all())

    def save(self, *args, **kwargs):
        self.duration = self.get_duration
        self.available_seats = self.get_available_seats
        super(Ride, self).save(*args, **kwargs)
