from collections import OrderedDict

from rest_framework import serializers

from cities.models import City
from cities.serializers import CitySerializer
from recurrent_rides.models import RecurrentRide
from rides.models import Ride, Participation, Coordinate
from users.serializers import UserSerializer
from vehicles.serializers import VehicleSerializer


class ParticipationListSerializer(serializers.ListSerializer):
    def to_representation(self, data):
        data = data.filter(decision='accepted')
        return super(ParticipationListSerializer, self).to_representation(data)


class ParticipationNestedSerializer(serializers.ModelSerializer):
    user = UserSerializer(many=False)

    class Meta:
        model = Participation
        fields = ('id', 'user', 'decision')
        list_serializer_class = ParticipationListSerializer


class CoordinatesNestedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Coordinate
        fields = ('lat', 'lng', 'sequence_no')


class RidePersonal(serializers.ModelSerializer):
    city_from = CitySerializer(many=False)
    city_to = CitySerializer(many=False)
    duration = serializers.SerializerMethodField()
    driver = UserSerializer(many=False)
    can_driver_edit = serializers.ReadOnlyField()

    class Meta:
        model = Ride
        fields = (
            'ride_id', 'city_from', 'city_to', 'area_from', 'area_to', 'start_date', 'duration', 'can_driver_edit',
            'driver', 'recurrent')
        extra_kwargs = {'area_from': {'required': False}, 'area_to': {'required': False}}

    def get_duration(self, obj):
        return get_duration(obj)


class RideListSerializer(serializers.ModelSerializer):
    city_from = CitySerializer(many=False)
    city_to = CitySerializer(many=False)
    driver = UserSerializer(many=False)
    duration = serializers.SerializerMethodField()

    class Meta:
        model = Ride
        fields = (
            'ride_id', 'city_from', 'city_to', 'area_from', 'area_to', 'start_date', 'price', 'seats', 'driver',
            'duration', 'available_seats')
        extra_kwargs = {'area_from': {'required': False}, 'area_to': {'required': False}}

    def get_duration(self, obj):
        return get_duration(obj)


class ParticipationSerializer(serializers.ModelSerializer):
    ride = RideListSerializer(many=False)
    user = UserSerializer(many=False)

    class Meta:
        model = Participation
        fields = ('id', 'ride', 'decision', 'reserved_seats', 'user')


class RideSerializer(serializers.ModelSerializer):
    city_from = CitySerializer(many=False)
    city_to = CitySerializer(many=False)
    driver = UserSerializer(many=False, required=False)
    vehicle = VehicleSerializer(many=False, required=False)
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
        if type(requested_city_from) is OrderedDict:
            city_from, _ = City.objects.get_or_create(**requested_city_from)
            instance.city_from = city_from

        requested_city_to = validated_data.get('city_to', instance.city_to)
        if type(requested_city_to) is OrderedDict:
            city_to, _ = City.objects.get_or_create(**requested_city_to)
            instance.city_to = city_to

        coordinates = validated_data.get('coordinates', instance.coordinates.all())
        new_coordinates = []
        for coordinate in coordinates:
            if type(coordinate) is OrderedDict:
                new_coordinates.append(
                    Coordinate.objects.get_or_create(ride=instance, lat=coordinate['lat'], lng=coordinate['lng'],
                                                     defaults={'sequence_no': coordinate['sequence_no']})[0])
            elif type(coordinate) is Coordinate:
                new_coordinates.append(coordinate)
        instance.coordinates.clear()

        for coordinate in new_coordinates:
            coordinate.ride = instance
            coordinate.save()

        update_data = {"duration": self.context.get('duration', instance.duration),
                       "vehicle": self.context.get('vehicle', instance.vehicle),
                       "area_from": validated_data.get('area_from', instance.area_from),
                       "area_to": validated_data.get('area_to', instance.area_to),
                       "start_date": validated_data.get('start_date', instance.start_date),
                       "price": validated_data.get('price', instance.price),
                       "seats": validated_data.get('seats', instance.seats),
                       "automatic_confirm": validated_data.get('automatic_confirm', instance.automatic_confirm),
                       "description": validated_data.get('description', instance.description)}
        update_ride(instance, update_data)
        return instance

    def create(self, validated_data, **kwargs):
        driver, vehicle, duration, city_from, city_to = get_ride_data(validated_data, self.context)
        coordinates = validated_data.pop('coordinates')

        ride = Ride(driver=driver, vehicle=vehicle, city_from=city_from, city_to=city_to, duration=duration,
                    **validated_data)
        ride.save()
        for coordinate in coordinates:
            Coordinate.objects.create(ride=ride, **coordinate)

        return ride

    def get_duration(self, obj):
        return get_duration(obj)


def get_duration(obj: Ride):
    total_minutes = int(obj.duration.total_seconds() // 60)
    hours = total_minutes // 60
    return {'hours': hours, 'minutes': total_minutes - hours * 60}


def update_ride(ride: Ride or RecurrentRide, update_data: dict):
    for key, value in update_data.items():
        setattr(ride, key, value)
    ride.save()


def get_ride_data(validated_data, context):
    driver = context['driver']
    vehicle = context['vehicle']
    duration = context['duration']

    city_from_data = validated_data.pop('city_from')
    city_from, _ = City.objects.get_or_create(**city_from_data)
    city_to_data = validated_data.pop('city_to')
    city_to, _ = City.objects.get_or_create(**city_to_data)

    return driver, vehicle, duration, city_from, city_to
