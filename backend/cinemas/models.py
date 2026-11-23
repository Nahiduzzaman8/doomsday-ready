from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.db.models import UniqueConstraint
from django.db.models.functions import Lower


class Cinema(models.Model):
    name = models.CharField(max_length=200)
    # Stored sorted ascending, with no duplicates (the serializer enforces both).
    bundle_sizes = ArrayField(models.PositiveSmallIntegerField())

    class Meta:
        ordering = ["name"]
        constraints = [
            UniqueConstraint(Lower("name"), name="unique_cinema_name_ci"),
        ]

    def __str__(self) -> str:
        return self.name
