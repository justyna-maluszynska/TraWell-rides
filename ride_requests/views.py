import datetime

from django.db.models import QuerySet
from django.http import JsonResponse
from django_filters import rest_framework as filters
from rest_framework import viewsets, status
from rest_framework.decorators import action

from ride_requests.filters import RequestFilter, RequestOrderFilter
from ride_requests.selectors import requests_list
from rides.models import Participation, Ride
from rides.serializers import ParticipationSerializer
from utils.CustomPagination import CustomPagination
from rides.utils.constants import ACTUAL_RIDES_ARGS
from utils.generic_endpoints import get_paginated_queryset
from utils.utils import verify_request
from utils.validate_token import validate_token


# Create your views here.
class RequestViewSet(viewsets.ModelViewSet):
    queryset = Participation.objects.filter(ride__is_cancelled=False, ride__start_date__gt=datetime.datetime.today())
    filter_backends = [filters.DjangoFilterBackend, RequestOrderFilter]
    filterset_class = RequestFilter
    pagination_class = CustomPagination
    serializer_class = ParticipationSerializer

    @validate_token
    def create(self, request, pk=None, *args, **kwargs):
        """
        Endpoint for sending request to join a ride.
        :param request:
        :param pk:
        :return:
        """
        user = kwargs['user']

        if not user.private:
            return JsonResponse(status=status.HTTP_405_METHOD_NOT_ALLOWED,
                                data=f"Company user not allowed to send request", safe=False)
        parameters = request.data
        try:
            seats_no = parameters['seats']
            ride_id = parameters['ride']
            ride = Ride.objects.get(ride_id=ride_id, **ACTUAL_RIDES_ARGS)
        except KeyError as e:
            return JsonResponse(status=status.HTTP_400_BAD_REQUEST, data=f"Missing parameter: {e}", safe=False)
        except Ride.DoesNotExist:
            return JsonResponse(status=status.HTTP_400_BAD_REQUEST, data=f"Ride {ride_id} not found", safe=False)

        is_correct, message = verify_request(user=user, ride=ride, seats=seats_no)

        if is_correct:
            decision = Participation.Decision.ACCEPTED if ride.automatic_confirm else Participation.Decision.PENDING

            Participation.objects.create(ride=ride, user=user, decision=decision, reserved_seats=seats_no)
            return JsonResponse(status=status.HTTP_200_OK, data='Request successfully sent', safe=False)
        else:
            return JsonResponse(status=status.HTTP_400_BAD_REQUEST, data=message, safe=False)

    @validate_token
    @action(detail=True, methods=['post'])
    def decision(self, request, *args, **kwargs):
        """
        Endpoint for drivers to accept or decline pending requests.
        :param request:
        :param args:
        :param kwargs:
        :return:
        """

        user = kwargs['user']

        instance = self.get_object()

        if instance.ride.driver == user:
            data = request.data
            try:
                if instance.decision == instance.Decision.PENDING:
                    decision = data['decision']
                    if decision in [choice[0] for choice in Participation.Decision.choices]:
                        instance.decision = decision
                        instance.save()
                        return JsonResponse(status=status.HTTP_200_OK,
                                            data=f'Request successfully changed to {decision}', safe=False)
                    else:
                        return JsonResponse(status=status.HTTP_400_BAD_REQUEST,
                                            data=f"Invalid decision parameter value", safe=False)
                return JsonResponse(status=status.HTTP_405_METHOD_NOT_ALLOWED,
                                    data=f"Request do not have {instance.Decision.PENDING} status", safe=False)
            except KeyError as e:
                return JsonResponse(status=status.HTTP_400_BAD_REQUEST, data=f"Missing parameter: {e}", safe=False)
        else:
            return JsonResponse(status=status.HTTP_405_METHOD_NOT_ALLOWED, data="User not allowed to delete request",
                                safe=False)

    @validate_token
    def destroy(self, request, *args, **kwargs):
        """
        Endpoint for removing sent requests
        :param request:
        :return:
        """
        user = kwargs['user']

        instance = self.get_object()

        if instance.user == user:
            if instance.decision != Participation.Decision.CANCELLED:
                instance.decision = Participation.Decision.CANCELLED
                instance.save()

                return JsonResponse(status=status.HTTP_200_OK, data=f'Request successfully cancelled', safe=False)

            return JsonResponse(status=status.HTTP_405_METHOD_NOT_ALLOWED, data=f"Request is already cancelled",
                                safe=False)

        return JsonResponse(status=status.HTTP_405_METHOD_NOT_ALLOWED, data="User not allowed to delete request",
                            safe=False)

    def _get_requests_list(self, request, rides: QuerySet, decision: str, additional_filters: dict = {}):
        requests = requests_list(request, queryset=self.get_queryset(), rides=rides, decision=decision,
                                 filters=additional_filters)
        filtered_requests = self.filter_queryset(requests)

        return get_paginated_queryset(self, filtered_requests)

    @validate_token
    @action(detail=False, methods=['get'])
    def my_requests(self, request, *args, **kwargs):
        user = kwargs['user']

        rides = Ride.objects.filter(passengers=user, **ACTUAL_RIDES_ARGS)
        decision = request.GET.get('decision', '')
        participation_filters = {"user": user}
        return self._get_requests_list(request=request, rides=rides, decision=decision,
                                       additional_filters=participation_filters)

    @validate_token
    @action(detail=False, methods=['get'])
    def pending_requests(self, request, *args, **kwargs):
        user = kwargs['user']

        rides = Ride.objects.filter(driver=user, **ACTUAL_RIDES_ARGS)
        return self._get_requests_list(request=request, rides=rides, decision='pending')
