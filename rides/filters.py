from django_filters import rest_framework as filters

from rides.models import Ride


class RideFilter(filters.FilterSet):
    class Meta:
        model = Ride
        fields = {
            'price': ['lt', 'gt'],
            'driver__avg_rate': ['gte'],
            'driver__private': ['exact']
        }
