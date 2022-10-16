from django.contrib import admin

from rides.models import Ride, RideAdmin

# Register your models here.

admin.site.register(Ride, RideAdmin)
