import datetime

from django_filters import rest_framework as filters, NumberFilter, DateTimeFilter, BooleanFilter, CharFilter

from rides.models import Ride


class RideFilter(filters.FilterSet):
    seats = NumberFilter(field_name='seats', lookup_expr='gte')
    start_date = DateTimeFilter(field_name='start_date', method='daterange_filter')
    price_from = NumberFilter(field_name='price', lookup_expr='gte')
    price_to = NumberFilter(field_name='price', lookup_expr='lte')
    driver_rate = NumberFilter(field_name='driver__avg_rate', lookup_expr='gte')
    ride_type = CharFilter(field_name='driver__private', method='driver_type_filter')

    class Meta:
        model = Ride
        fields = ('seats', 'start_date', 'price_from', 'price_to', 'driver_rate', 'ride_type')

    def daterange_filter(self, queryset, name: str, value: datetime):
        first_parameter = '__'.join([name, 'gte'])
        second_parameter = '__'.join([name, 'lte'])
        return queryset.filter(**{first_parameter: value,
                                  second_parameter: datetime.datetime.combine(value.date() + datetime.timedelta(1),
                                                                              datetime.time.max)})

    def driver_type_filter(self, queryset, name: str, value: str):
        if value == 'all' or value is None:
            return queryset
        if value == 'private':
            return queryset.filter(**{'driver__private': True})
        if value == 'company':
            return queryset.filter(**{'driver__private': False})
