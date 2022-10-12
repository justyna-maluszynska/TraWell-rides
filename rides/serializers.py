from rest_framework import serializers

from cities.models import City
from rides.models import Ride
from users.models import User
from vehicles.models import Vehicle


class CityNestedSerializer(serializers.ModelSerializer):
    class Meta:
        model = City
        fields = ('city_id', 'name', 'county', 'state', 'lat', 'lng')


class VehicleNestedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vehicle
        fields = ('vehicle_id', 'make', 'model', 'color')


class UserNestedSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('user_id', 'first_name', 'last_name', 'avg_rate')


class RideSerializer(serializers.ModelSerializer):
    city_from = CityNestedSerializer(many=False)
    city_to = CityNestedSerializer(many=False)
    driver = UserNestedSerializer(many=False)
    vehicle = VehicleNestedSerializer(many=False)

    class Meta:
        model = Ride
        fields = ('ride_id', 'city_from', 'city_to', 'area_from', 'area_to', 'start_date', 'end_date', 'price', 'seats',
                  'recurrent', 'automatic_confirm', 'description', 'driver', 'vehicle')
        extra_kwargs = {'area_from': {'required': False}, 'area_to': {'required': False},
                        'description': {'required': False}}
