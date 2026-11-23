from rest_framework import serializers


class StrictIntegerField(serializers.IntegerField):
    """Accepts only real JSON integers. DRF alone would accept "126" as 126."""

    def to_internal_value(self, data):
        if isinstance(data, bool) or not isinstance(data, int):
            self.fail("invalid")
        return super().to_internal_value(data)


class StrictBooleanField(serializers.BooleanField):
    """Accepts only real JSON booleans. DRF alone would accept "true", 1 or "yes"."""

    def to_internal_value(self, data):
        if not isinstance(data, bool):
            self.fail("invalid", input=data)
        return data
