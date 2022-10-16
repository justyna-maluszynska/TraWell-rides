import datetime

from django.http import JsonResponse
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination

from cities.models import City
from rides.filters import RideFilter
from rides.models import Ride
from rides.serializers import RideSerializer
from django_filters import rest_framework as filters
from rest_framework.filters import OrderingFilter

from rides.utils import validate_hours_minutes
from users.models import User


class CustomRidePagination(PageNumberPagination):
    page_size = 15
    page_size_query_param = 'page_size'


class RideViewSet(viewsets.ModelViewSet):
    """
    API View Set that allows Rides to be viewed, created, updated or deleted.
    This viewset automatically provides list and detail actions.
    """
    serializer_class = RideSerializer
    queryset = Ride.objects.filter(start_date__gt=datetime.datetime.today())
    filter_backends = [filters.DjangoFilterBackend, OrderingFilter]
    filterset_class = RideFilter
    pagination_class = CustomRidePagination
    ordering_fields = ['price', 'start_date', 'duration', 'available_seats']

    # TODO authorization
    def update(self, request, *args, **kwargs):
        """
        Endpoint for updating Ride object.
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        if request.method == 'PATCH':
            instance = self.get_object()
            update_data = request.data

            requested_city_from = update_data.pop('city_from')
            city_from, was_created = City.objects.get_or_create(**requested_city_from)
            instance.city_from = city_from

            requested_city_to = update_data.pop('city_to')
            city_to, was_created = City.objects.get_or_create(**requested_city_to)
            instance.city_to = city_to

            duration = update_data.pop('duration')
            hours = duration['hours']
            minutes = duration['minutes']
            if validate_hours_minutes(hours, minutes):
                instance.duration = datetime.timedelta(hours=hours, minutes=minutes)
            else:
                return JsonResponse(status=status.HTTP_400_BAD_REQUEST, data="Wrong parameters", safe=False)

            serializer = self.get_serializer(instance=instance, data=update_data, partial=True)
            if serializer.is_valid():
                serializer.save()
                instance.save()
                serializer = self.get_serializer(instance)
                return JsonResponse(serializer.data, safe=False)

            return JsonResponse(status=status.HTTP_400_BAD_REQUEST, data="Wrong parameters", safe=False)

        return super().update(request, *args, **kwargs)

    @action(detail=True, methods=['get'])
    def user_rides(self, request, pk=None):
        """
        Endpoint for getting user rides
        :param request:
        :param pk: User ID
        :return: List of user's rides.
        """
        try:
            driver = User.objects.get(user_id=pk)
        except User.DoesNotExist:
            return JsonResponse(status=status.HTTP_404_NOT_FOUND, data="User not found", safe=False)

        rides = Ride.objects.filter(driver=driver)
        serializer = self.get_serializer(rides, many=True)
        return JsonResponse(serializer.data, safe=False)
