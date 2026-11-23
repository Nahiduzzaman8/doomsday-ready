from rest_framework import serializers

from cinemas.models import Cinema
from movies.serializers import StrictIntegerField


class CinemaInputSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=200)
    bundle_sizes = serializers.ListField(
        child=StrictIntegerField(min_value=1, max_value=500),
        min_length=1,
        max_length=10,
    )

    def validate_bundle_sizes(self, value: list[int]) -> list[int]:
        if len(set(value)) != len(value):
            raise serializers.ValidationError("Bundle sizes must all be different.")
        return sorted(value)


class CinemaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cinema
        fields = ["id", "name", "bundle_sizes"]
