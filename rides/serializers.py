import datetime

from rest_framework import serializers

from cities.models import City
from rides.models import Ride, Participation, Coordinate
from users.models import User
from vehicles.models import Vehicle


class CityNestedSerializer(serializers.ModelSerializer):
    class Meta:
        model = City
        fields = ('city_id', 'name', 'county', 'state', 'lat', 'lng')

    def create(self, validated_data):
        instance, _ = City.objects.get_or_create(**validated_data)
        return instance


class VehicleNestedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vehicle
        fields = ('vehicle_id', 'make', 'model', 'color')


class UserNestedSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('user_id', 'first_name', 'last_name', 'avg_rate', 'avatar', 'private')


class ParticipationNestedSerializer(serializers.ModelSerializer):
    user = UserNestedSerializer(many=False)

    class Meta:
        model = Participation
        fields = ('id', 'user', 'decision')


class CoordinatesNestedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Coordinate
        fields = ('lat', 'lng', 'sequence_no')


class RidePersonal(serializers.ModelSerializer):
    city_from = CityNestedSerializer(many=False)
    city_to = CityNestedSerializer(many=False)
    duration = serializers.SerializerMethodField()
    driver = UserNestedSerializer(many=False)
    can_driver_edit = serializers.ReadOnlyField()

    class Meta:
        model = Ride
        fields = (
            'ride_id', 'city_from', 'city_to', 'area_from', 'area_to', 'start_date', 'duration', 'can_driver_edit',
            'driver', 'recurrent')
        extra_kwargs = {'area_from': {'required': False}, 'area_to': {'required': False}}

    def get_duration(self, obj):
        return get_duration(obj)

    def validate_duration(self, value):
        return validate_duration(value)

    def validate_start_date(self, value):
        if value < datetime.datetime.now():
            raise serializers.ValidationError("Start date cannot be in the past")
        return value


class RideListSerializer(serializers.ModelSerializer):
    city_from = CityNestedSerializer(many=False)
    city_to = CityNestedSerializer(many=False)
    driver = UserNestedSerializer(many=False)
    duration = serializers.SerializerMethodField()

    class Meta:
        model = Ride
        fields = (
            'ride_id', 'city_from', 'city_to', 'area_from', 'area_to', 'start_date', 'price', 'seats', 'driver',
            'duration', 'available_seats')
        extra_kwargs = {'area_from': {'required': False}, 'area_to': {'required': False}}

    def get_duration(self, obj):
        return get_duration(obj)

    def validate_duration(self, value):
        return validate_duration(value)

    def validate_start_date(self, value):
        if value < datetime.datetime.now():
            raise serializers.ValidationError("Start date cannot be in the past")
        return value


class RideSerializer(serializers.ModelSerializer):
    city_from = CityNestedSerializer(many=False)
    city_to = CityNestedSerializer(many=False)
    driver = UserNestedSerializer(many=False, required=False)
    vehicle = VehicleNestedSerializer(many=False, required=False)
    duration = serializers.SerializerMethodField()
    passengers = ParticipationNestedSerializer(source='participation_set', many=True, required=False)
    coordinates = CoordinatesNestedSerializer(many=True, required=False)

    class Meta:
        model = Ride
        fields = ('ride_id', 'city_from', 'city_to', 'area_from', 'area_to', 'start_date', 'price', 'seats',
                  'recurrent', 'automatic_confirm', 'description', 'driver', 'vehicle', 'duration', 'available_seats',
                  'passengers', 'coordinates')
        depth = 1

    def create(self, validated_data, **kwargs):
        driver = self.context['driver']
        vehicle = self.context['vehicle']

        city_from_data = validated_data.pop('city_from')
        city_from, _ = City.objects.get_or_create(**city_from_data)
        city_to_data = validated_data.pop('city_to')
        city_to, _ = City.objects.get_or_create(**city_to_data)

        coordinates = validated_data.pop('coordinates')

        ride = Ride(driver=driver, vehicle=vehicle, city_from=city_from, city_to=city_to, **validated_data)
        ride.save()
        for coordinate in coordinates:
            Coordinate.objects.create(ride=ride, **coordinate)

        return ride

    def get_duration(self, obj):
        return get_duration(obj)

    def validate_duration(self, value):
        return validate_duration(value)

    # def validate_start_date(self, value):
    #     if value < datetime.datetime.now():
    #         raise serializers.ValidationError("Start date cannot be in the past")
    #     return value


def get_duration(obj: Ride):
    total_minutes = int(obj.duration.total_seconds() // 60)
    hours = total_minutes // 60
    return {'hours': hours, 'minutes': total_minutes - hours * 60}


def validate_duration(value: dict):
    try:
        hours = value['hours']
        minutes = value['minutes']
        if 0 > hours or 0 > minutes >= 60:
            raise serializers.ValidationError("Invalid values of ride duration field")
        return value
    except KeyError:
        raise serializers.ValidationError("Invalid structure of ride duration field")
