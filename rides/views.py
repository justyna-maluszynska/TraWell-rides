import datetime

from django.db.models import QuerySet
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

from rides.utils import validate_hours_minutes, find_city_object, find_near_cities, get_city_info


class CustomRidePagination(PageNumberPagination):
    page_size = 15
    page_size_query_param = 'page_size'


class RideViewSet(viewsets.ModelViewSet):
    """
    API View Set that allows Rides to be viewed, created, updated or deleted.
    This viewset automatically provides list and detail actions.
    """
    serializer_class = RideSerializer
    queryset = Ride.objects.filter()
    filter_backends = [filters.DjangoFilterBackend, OrderingFilter]
    filterset_class = RideFilter
    pagination_class = CustomRidePagination
    ordering_fields = ['price', 'start_date', 'duration', 'available_seats']

    def _get_queryset_with_near_cities(self, city_from: dict, city_to: dict) -> QuerySet:
        """
        Gets queryset with cities near the starting city (city_from). The accepted range in km is defined in MAX_DISTANCE.

        :param city_from: dictionary with starting city data
        :param city_to: dictionary with destination city data
        :return: queryset with all rides from city_from + nearest cities to city_to
        """
        city_from_obj = find_city_object(city_from)
        city_to_obj = find_city_object(city_to)

        queryset = Ride.objects.filter(start_date__gt=datetime.datetime.today(), city_to__name=city_to_obj.name,
                                       city_to__state=city_to_obj.state, city_to__county=city_to_obj.county)

        if not queryset.exists():
            # There are no rides to given city destination, no sense to check the rest of parameters
            return queryset

        near_cities_ids = find_near_cities(city_from_obj)

        queryset_with_near_cities = queryset.filter(city_from__city_id__in=near_cities_ids)
        filtered_queryset = self.filter_queryset(queryset_with_near_cities)
        return filtered_queryset

    @action(detail=False, methods=['get'])
    def get_filtered(self, request, *args, **kwargs):
        """
        Endpoint for getting filtered rides.
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        parameters = request.GET
        try:
            city_from_dict = get_city_info(parameters, 'from')
            city_to_dict = get_city_info(parameters, 'to')
        except KeyError as e:
            return JsonResponse(status=status.HTTP_400_BAD_REQUEST, data=f"Missing parameter {e}", safe=False)

        filtered_queryset = self._get_queryset_with_near_cities(city_from_dict, city_to_dict)
        page = self.paginate_queryset(filtered_queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(page, many=True)
        return JsonResponse(serializer.data, safe=False)

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

            if not instance.passengers.filter(passenger__decision__in=['accepted', 'pending']):
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
            else:
                return JsonResponse(status=status.HTTP_405_METHOD_NOT_ALLOWED, data="Cannot edit ride data", safe=False)

        return super().update(request, *args, **kwargs)
