from rest_framework import serializers

from cinemas.models import Cinema
from config.fields import StrictIntegerField


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


class GroupSizeField(serializers.IntegerField):
    """Accepts only whole-number strings like "11". DRF alone would accept "11.0" or " 11 "."""

    def to_internal_value(self, data):
        if not (data.isascii() and data.isdigit()):
            self.fail("invalid")
        return super().to_internal_value(data)


class BookingQuerySerializer(serializers.Serializer):
    groupSize = GroupSizeField(min_value=1, max_value=10_000)


class CinemaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cinema
        fields = ["id", "name", "bundle_sizes"]
