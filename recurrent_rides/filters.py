import datetime

from django_filters import rest_framework as filters, DateTimeFilter

from recurrent_rides.models import RecurrentRide
from utils.utils import daterange_filter


class RecurrentRideFilter(filters.FilterSet):
    start_date = DateTimeFilter(field_name='start_date', method='daterange_filter')

    class Meta:
        model = RecurrentRide
        fields = ('start_date',)

    def daterange_filter(self, queryset, name: str, value: datetime):
        return daterange_filter(queryset, name, value)
