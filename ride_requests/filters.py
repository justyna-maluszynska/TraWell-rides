import datetime

from django_filters import rest_framework as filters, DateTimeFilter
from rest_framework.filters import OrderingFilter

from rides.filters import daterange_filter
from rides.models import Participation


class RequestFilter(filters.FilterSet):
    start_date = DateTimeFilter(field_name='ride__start_date', method='daterange_filter')

    class Meta:
        model = Participation
        fields = ('start_date',)

    def daterange_filter(self, queryset, name: str, value: datetime):
        return daterange_filter(queryset, name, value)


class RequestOrderFilter(OrderingFilter):
    allowed_custom_filters = ['price', 'start_date', 'duration', 'available_seats']
    fields_related = {
        'start_date': 'ride__start_date',
        'duration': 'ride__duration',
        'available_seats': 'ride__available_seats',
        'price': 'ride__price'
    }

    def get_ordering(self, request, queryset, view):
        params = request.query_params.get(self.ordering_param)
        if params:
            fields = [param.strip() for param in params.split(',')]
            ordering = [f for f in fields if f.lstrip('-') in self.allowed_custom_filters]
            if ordering:
                return ordering

        return self.get_default_ordering(view)

    def filter_queryset(self, request, queryset, view):
        order_fields = []
        ordering = self.get_ordering(request, queryset, view)
        if ordering:
            for field in ordering:
                symbol = "-" if "-" in field else ""
                order_fields.append(symbol + self.fields_related[field.lstrip('-')])
        if order_fields:
            return queryset.order_by(*order_fields)

        return queryset
