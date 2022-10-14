from rest_framework import viewsets

from rides.filters import RideFilter
from rides.models import Ride
from rides.serializers import RideSerializer
from rest_framework.decorators import action
from django_filters import rest_framework as filters


class RideViewSet(viewsets.ModelViewSet):
    """
    API View Set that allows Rides to be viewed, created, updated or deleted.
    """
    serializer_class = RideSerializer
    queryset = Ride.objects.all()
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = RideFilter
