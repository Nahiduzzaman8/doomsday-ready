from django.db import IntegrityError, transaction
from django.db.models import QuerySet
from django.shortcuts import get_object_or_404

from cinemas.bundles import fewest_bundles
from cinemas.models import Cinema
from config.exceptions import AlreadyExists

NAME_CONSTRAINT = "unique_cinema_name_ci"
NAME_TAKEN = "A cinema with this name already exists."


def list_cinemas() -> QuerySet[Cinema]:
    return Cinema.objects.all()


def get_cinema(cinema_id: int) -> Cinema:
    return get_object_or_404(Cinema, pk=cinema_id)


def create_cinema(validated_data: dict) -> Cinema:
    try:
        # A savepoint, so a failed insert does not break a surrounding transaction.
        with transaction.atomic():
            return Cinema.objects.create(**validated_data)
    except IntegrityError as error:
        if NAME_CONSTRAINT in str(error):
            raise AlreadyExists(NAME_TAKEN) from error
        raise


def get_booking_quote(cinema: Cinema, group_size: int) -> dict:
    result = fewest_bundles(cinema.bundle_sizes, group_size)
    quote = {"cinema": {"id": cinema.id, "name": cinema.name}, "group_size": group_size}

    if result is None:
        return {
            **quote,
            "possible": False,
            "total_bundles": None,
            "bundles": [],
            "message": f"No combination of bundles adds up to exactly {group_size} seats.",
        }

    return {
        **quote,
        "possible": True,
        "total_bundles": sum(count for _, count in result),
        "bundles": [{"size": size, "count": count} for size, count in result],
    }
