from django.db import models
from django.db.models import CheckConstraint, Q, UniqueConstraint
from django.db.models.functions import Lower


class Movie(models.Model):
    title = models.CharField(max_length=200)
    release_year = models.PositiveSmallIntegerField()
    runtime_minutes = models.PositiveSmallIntegerField()
    watched = models.BooleanField(default=False)
    # A link from_movie -> to_movie means: watch to_movie before from_movie.
    prerequisites = models.ManyToManyField(
        "self", symmetrical=False, related_name="required_for", blank=True
    )

    class Meta:
        ordering = ["release_year", "title"]
        constraints = [
            UniqueConstraint(Lower("title"), name="unique_movie_title_ci"),
            CheckConstraint(
                condition=Q(runtime_minutes__gte=1, runtime_minutes__lte=300),
                name="movie_runtime_range",
            ),
            CheckConstraint(
                condition=Q(release_year__gte=1900, release_year__lte=2100),
                name="movie_release_year_range",
            ),
        ]

    def __str__(self) -> str:
        return self.title
