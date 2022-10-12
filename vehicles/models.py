from django.db import models


class Vehicle(models.Model):
    vehicle_id = models.AutoField(primary_key=True)
    make = models.CharField(max_length=20, null=False)
    model = models.CharField(max_length=30, null=False)
    color = models.CharField(max_length=20)
