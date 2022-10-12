from rest_framework import serializers

from cities.models import City


class CitySerializer(serializers.ModelSerializer):
    class Meta:
        model = City
        fields = ('city_id', 'name', 'county', 'state', 'lat', 'lng')
