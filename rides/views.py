from rest_framework import viewsets

from rides.models import Ride
from rides.serializers import RideSerializer


class RideViewSet(viewsets.ModelViewSet):
    """
    API View Set that allows Rides to be viewed, created, updated or deleted.
    """
    serializer_class = RideSerializer
    queryset = Ride.objects.all()
