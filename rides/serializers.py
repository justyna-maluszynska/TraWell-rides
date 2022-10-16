from rest_framework import serializers

from cities.models import City
from rides.models import Ride, Participation
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
        fields = ('user_id', 'first_name', 'last_name', 'avg_rate', 'avatar')


class ParticipationNestedSerializer(serializers.ModelSerializer):
    user = UserNestedSerializer(many=False)

    class Meta:
        model = Participation
        fields = ('user', 'decision')


class RideSerializer(serializers.ModelSerializer):
    city_from = CityNestedSerializer(many=False)
    city_to = CityNestedSerializer(many=False)
    driver = UserNestedSerializer(many=False)
    vehicle = VehicleNestedSerializer(many=False)
    duration = serializers.SerializerMethodField()
    passengers = ParticipationNestedSerializer(source='participation_set', many=True)

    class Meta:
        model = Ride
        fields = ('ride_id', 'city_from', 'city_to', 'area_from', 'area_to', 'start_date', 'price', 'seats',
                  'recurrent', 'automatic_confirm', 'description', 'driver', 'vehicle', 'duration', 'available_seats',
                  'passengers')
        extra_kwargs = {'area_from': {'required': False}, 'area_to': {'required': False},
                        'description': {'required': False}}

    def get_duration(self, obj):
        total_minutes = int(obj.duration.total_seconds() // 60)
        hours = total_minutes // 60
        return {'hours': hours, 'minutes': total_minutes - hours * 60}
