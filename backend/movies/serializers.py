from rest_framework import serializers

from config.fields import StrictBooleanField, StrictIntegerField
from movies.models import Movie


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


class RewatchPlanSerializer(serializers.Serializer):
    target = serializers.DictField()
    movies = MovieSerializer(many=True)
    total_count = serializers.IntegerField()
    watched_count = serializers.IntegerField()
    unwatched_runtime_minutes = serializers.IntegerField()
