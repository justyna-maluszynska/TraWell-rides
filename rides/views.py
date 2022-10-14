from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination

from rides.filters import RideFilter
from rides.models import Ride
from rides.serializers import RideSerializer
from django_filters import rest_framework as filters


class CustomRidePagination(PageNumberPagination):
    page_size = 15
    page_size_query_param = 'page_size'


class RideViewSet(viewsets.ModelViewSet):
    """
    API View Set that allows Rides to be viewed, created, updated or deleted.
    """
    serializer_class = RideSerializer
    queryset = Ride.objects.all()
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = RideFilter
    pagination_class = CustomRidePagination
