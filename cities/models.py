from django.db import models


class City(models.Model):
    city_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=80, null=False)
    county = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    lat = models.DecimalField(null=False, max_digits=15, decimal_places=7)
    lng = models.DecimalField(null=False, max_digits=15, decimal_places=7)
