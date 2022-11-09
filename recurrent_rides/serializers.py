from rest_framework import serializers

from cities.serializers import CitySerializer
from recurrent_rides.models import RecurrentRide
from rides.models import Ride
from rides.serializers import get_ride_data, update_ride, get_duration
from rides.utils.constants import ACTUAL_RIDES_ARGS
from users.serializers import UserSerializer
from vehicles.serializers import VehicleSerializer


class RecurrentRideSerializer(serializers.ModelSerializer):
    city_from = CitySerializer(many=False)
    city_to = CitySerializer(many=False)
    driver = UserSerializer(many=False, required=False)
    vehicle = VehicleSerializer(many=False, required=False)
    duration = serializers.SerializerMethodField()

    class Meta:
        model = RecurrentRide
        fields = (
            'ride_id', 'city_from', 'city_to', 'area_from', 'area_to', 'start_date', 'end_date', 'frequency_type',
            'frequence', 'occurrences', 'price', 'seats', 'automatic_confirm', 'description', 'driver', 'vehicle',
            'duration')
        depth = 1

    def create(self, validated_data, **kwargs):
        driver, vehicle, duration, city_from, city_to = get_ride_data(validated_data, self.context)

        recurrent_ride = RecurrentRide(driver=driver, vehicle=vehicle, city_from=city_from, city_to=city_to,
                                       duration=duration, **validated_data)
        recurrent_ride.save()

        return recurrent_ride

    def update(self, instance, validated_data, **kwargs):
        vehicle = self.context.get('vehicle', instance.vehicle)
        automatic_confirm = validated_data.get('automatic_confirm', instance.automatic_confirm)
        description = validated_data.get('description', instance.description)
        seats = validated_data.get('seats', instance.seats)

        update_data = {'vehicle': vehicle, 'automatic_confirm': automatic_confirm, 'description': description,
                       'seats': seats}
        update_ride(instance, update_data)

        single_rides = Ride.objects.filter(recurrent_ride=instance, **ACTUAL_RIDES_ARGS)
        for ride in single_rides:
            update_ride(ride, update_data)

        return instance

    def get_duration(self, obj):
        return get_duration(obj)


class RecurrentRidePersonal(serializers.ModelSerializer):
    city_from = CitySerializer(many=False)
    city_to = CitySerializer(many=False)
    duration = serializers.SerializerMethodField()
    driver = UserSerializer(many=False)
    can_driver_edit = True

    class Meta:
        model = Ride
        fields = (
            'ride_id', 'city_from', 'city_to', 'area_from', 'area_to', 'start_date', 'duration', 'can_driver_edit',
            'driver')
        extra_kwargs = {'area_from': {'required': False}, 'area_to': {'required': False}}

    def get_duration(self, obj):
        return get_duration(obj)


class SingleRideSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ride
        fields = ('ride_id', 'start_date')
