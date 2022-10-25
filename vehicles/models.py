from django.db import models

from users.models import User


class Vehicle(models.Model):
    vehicle_id = models.AutoField(primary_key=True)
    make = models.CharField(max_length=20, null=False)
    model = models.CharField(max_length=30, null=False)
    color = models.CharField(max_length=20)
    user = models.ForeignKey(User, related_name='vehicles', on_delete=models.CASCADE, blank=False, null=True)
    # default is temporary
