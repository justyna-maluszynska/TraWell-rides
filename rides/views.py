from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination

from rides.filters import RideFilter
from rides.models import Ride
from rides.serializers import RideSerializer
from django_filters import rest_framework as filters
from rest_framework.filters import OrderingFilter


class CustomRidePagination(PageNumberPagination):
    page_size = 15
    page_size_query_param = 'page_size'


class RideViewSet(viewsets.ModelViewSet):
    """
    API View Set that allows Rides to be viewed, created, updated or deleted.
    This viewset automatically provides list and detail actions.
    """
    serializer_class = RideSerializer
    queryset = Ride.objects.all()
    filter_backends = [filters.DjangoFilterBackend, OrderingFilter]
    filterset_class = RideFilter
    pagination_class = CustomRidePagination
    ordering_fields = ['price', 'start_date', 'duration', 'available_seats']
