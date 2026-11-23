from rest_framework import serializers

from movies.models import Movie


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


class MovieInputSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=200)
    release_year = StrictIntegerField(min_value=1900, max_value=2100)
    runtime_minutes = StrictIntegerField(min_value=1, max_value=300)
    watched = StrictBooleanField(default=False)
    prerequisites = serializers.ListField(child=StrictIntegerField(), default=list)

    def validate_prerequisites(self, value: list[int]) -> list[int]:
        unique_ids = list(dict.fromkeys(value))
        found = set(Movie.objects.filter(id__in=unique_ids).values_list("id", flat=True))
        missing = [movie_id for movie_id in unique_ids if movie_id not in found]
        if missing:
            listed = ", ".join(str(movie_id) for movie_id in missing)
            raise serializers.ValidationError(f"Unknown movie ids: {listed}.")
        return unique_ids


class MovieSerializer(serializers.ModelSerializer):
    # Movie.Meta.ordering makes these come out sorted by (release_year, title).
    prerequisites = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta:
        model = Movie
        fields = ["id", "title", "release_year", "runtime_minutes", "watched", "prerequisites"]
