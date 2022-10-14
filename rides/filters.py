from django_filters import rest_framework as filters, AllValuesFilter, NumberFilter, DateTimeFilter, BooleanFilter, \
    CharFilter

from rides.models import Ride


class RideFilter(filters.FilterSet):
    city_from = CharFilter(field_name='city_from__name', lookup_expr='exact')
    city_to = CharFilter(field_name='city_to__name', lookup_expr='exact')
    seats = NumberFilter(field_name='seats', lookup_expr='gte')
    start_date = DateTimeFilter(field_name='start_date', lookup_expr='gte')
    price_from = NumberFilter(field_name='price', lookup_expr='gte')
    price_to = NumberFilter(field_name='price', lookup_expr='lte')
    driver_rate = NumberFilter(field_name='driver__avg_rate', lookup_expr='gte')
    is_ride_private = BooleanFilter(field_name='driver__private', lookup_expr='exact')

    class Meta:
        model = Ride
        fields = (
            'city_from', 'city_to', 'seats', 'start_date', 'price_from', 'price_to', 'driver_rate', 'is_ride_private'
        )
