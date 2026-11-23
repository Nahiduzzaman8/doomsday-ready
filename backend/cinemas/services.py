from django.db import IntegrityError, transaction
from django.db.models import QuerySet

from cinemas.models import Cinema
from config.exceptions import AlreadyExists

NAME_CONSTRAINT = "unique_cinema_name_ci"
NAME_TAKEN = "A cinema with this name already exists."


def list_cinemas() -> QuerySet[Cinema]:
    return Cinema.objects.all()


def create_cinema(validated_data: dict) -> Cinema:
    try:
        # A savepoint, so a failed insert does not break a surrounding transaction.
        with transaction.atomic():
            return Cinema.objects.create(**validated_data)
    except IntegrityError as error:
        if NAME_CONSTRAINT in str(error):
            raise AlreadyExists(NAME_TAKEN) from error
        raise
