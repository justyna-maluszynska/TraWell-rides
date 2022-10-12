from rest_framework import serializers

from vehicles.models import Vehicle


class VehicleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vehicle
        fields = ('vehicle_id', 'make', 'model', 'color')

