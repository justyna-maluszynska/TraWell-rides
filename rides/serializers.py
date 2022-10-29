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

    def validate_start_date(self, value):
        if value < datetime.datetime.now():
            raise serializers.ValidationError("Start date cannot be in the past")
        return value


class ParticipationSerializer(serializers.ModelSerializer):
    ride = RideListSerializer(many=False)

    class Meta:
        model = Participation
        fields = ('id', 'ride', 'decision', 'reserved_seats')


class RideSerializer(serializers.ModelSerializer):
    city_from = CityNestedSerializer(many=False)
    city_to = CityNestedSerializer(many=False)
    driver = UserNestedSerializer(many=False, required=False)
    vehicle = VehicleNestedSerializer(many=False, required=False)
    duration = serializers.SerializerMethodField()
    passengers = ParticipationNestedSerializer(source='participation_set', many=True, required=False)
    coordinates = CoordinatesNestedSerializer(many=True)

    class Meta:
        model = Ride
        fields = ('ride_id', 'city_from', 'city_to', 'area_from', 'area_to', 'start_date', 'price', 'seats',
                  'recurrent', 'automatic_confirm', 'description', 'driver', 'vehicle', 'duration', 'available_seats',
                  'passengers', 'coordinates')
        depth = 1

    def update(self, instance, validated_data, **kwargs):
        requested_city_from = validated_data.get('city_from', instance.city_from)
        if type(requested_city_from) is dict:
            city_from, was_created = City.objects.get_or_create(**requested_city_from)
            instance.city_from = city_from

        requested_city_to = validated_data.get('city_to', instance.city_to)
        if type(requested_city_to) is dict:
            city_to, was_created = City.objects.get_or_create(**requested_city_to)
            instance.city_to = city_to

        # instance.coordinates.all().delete()
        # coordinates = validated_data.get('coordinates')
        #
        # for coordinate in coordinates:
        #     Coordinate.objects.update_or_create(ride=instance, lat=coordinate['lat'], lng=coordinate['lng'],
        #                                         defaults={'sequence_no': coordinate['sequence_no']})

        instance.duration = self.context.get('duration', instance.duration)
        instance.vehicle = self.context.get('vehicle', instance.vehicle)
        instance.area_from = validated_data.get('area_from', instance.area_from)
        instance.area_to = validated_data.get('area_to', instance.area_to)
        instance.start_date = validated_data.get('start_date', instance.start_date)
        instance.price = validated_data.get('price', instance.price)
        instance.seats = validated_data.get('seats', instance.seats)
        instance.automatic_confirm = validated_data.get('automatic_confirm', instance.automatic_confirm)
        instance.description = validated_data.get('description', instance.description)
        instance.save()
        return instance

    def create(self, validated_data, **kwargs):
        driver = self.context['driver']
        vehicle = self.context['vehicle']
        duration = self.context['duration']

        city_from_data = validated_data.pop('city_from')
        city_from, _ = City.objects.get_or_create(**city_from_data)
        city_to_data = validated_data.pop('city_to')
        city_to, _ = City.objects.get_or_create(**city_to_data)

        coordinates = validated_data.pop('coordinates')

        ride = Ride(driver=driver, vehicle=vehicle, city_from=city_from, city_to=city_to, duration=duration,
                    **validated_data)
        ride.save()
        for coordinate in coordinates:
            Coordinate.objects.create(ride=ride, **coordinate)

        return ride

    def get_duration(self, obj):
        return get_duration(obj)

    # def validate_start_date(self, value):
    #     if value < datetime.datetime.now():
    #         raise serializers.ValidationError("Start date cannot be in the past")
    #     return value


def get_duration(obj: Ride):
    total_minutes = int(obj.duration.total_seconds() // 60)
    hours = total_minutes // 60
    return {'hours': hours, 'minutes': total_minutes - hours * 60}
