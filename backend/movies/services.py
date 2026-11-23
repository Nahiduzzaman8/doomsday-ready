from django.db import IntegrityError, transaction
from django.db.models import QuerySet
from django.shortcuts import get_object_or_404

from config.exceptions import AlreadyExists, CircularDependency
from movies.graph import creates_cycle, rewatch_order
from movies.models import Movie

TITLE_CONSTRAINT = "unique_movie_title_ci"
TITLE_TAKEN = "A movie with this title already exists."


def list_movies() -> QuerySet[Movie]:
    return Movie.objects.prefetch_related("prerequisites")


def get_movie(movie_id: int) -> Movie:
    return get_object_or_404(list_movies(), pk=movie_id)


def load_graph() -> dict[int, list[int]]:
    graph = {movie_id: [] for movie_id in Movie.objects.values_list("id", flat=True)}
    links = Movie.prerequisites.through.objects.order_by(
        "to_movie__release_year", "to_movie__title"
    ).values_list("from_movie_id", "to_movie_id")
    for movie_id, prerequisite_id in links:
        graph[movie_id].append(prerequisite_id)
    return graph


def create_movie(validated_data: dict) -> Movie:
    fields = dict(validated_data)
    prerequisite_ids = fields.pop("prerequisites")
    try:
        with transaction.atomic():
            movie = Movie.objects.create(**fields)
            _apply_prerequisites(movie, prerequisite_ids)
    except IntegrityError as error:
        _raise_if_title_taken(error)
        raise
    return movie


def update_movie(movie: Movie, validated_data: dict) -> Movie:
    fields = dict(validated_data)
    try:
        with transaction.atomic():
            # Only a prerequisite change can create a cycle, so only that path takes the lock.
            if "prerequisites" in fields:
                _apply_prerequisites(movie, fields.pop("prerequisites"))
            for name, value in fields.items():
                setattr(movie, name, value)
            movie.save()
    except IntegrityError as error:
        _raise_if_title_taken(error)
        raise
    return movie


def get_rewatch_plan(movie: Movie) -> dict:
    ids = rewatch_order(load_graph(), movie.id)
    movies_by_id = list_movies().in_bulk(ids)
    movies = [movies_by_id[movie_id] for movie_id in ids]
    unwatched = [entry for entry in movies if not entry.watched]
    return {
        "target": {"id": movie.id, "title": movie.title},
        "movies": movies,
        "total_count": len(movies),
        "watched_count": len(movies) - len(unwatched),
        "unwatched_runtime_minutes": sum(entry.runtime_minutes for entry in unwatched),
    }


def _apply_prerequisites(movie: Movie, prerequisite_ids: list[int]) -> None:
    # Locking every movie row makes parallel prerequisite updates run one after another,
    # so two requests cannot each pass the cycle check and together build a cycle.
    list(Movie.objects.select_for_update().order_by("id").values_list("id", flat=True))
    graph = load_graph()
    if creates_cycle(graph, movie.id, prerequisite_ids):
        raise CircularDependency()
    movie.prerequisites.set(prerequisite_ids)


def _raise_if_title_taken(error: IntegrityError) -> None:
    if TITLE_CONSTRAINT in str(error):
        raise AlreadyExists(TITLE_TAKEN) from error
