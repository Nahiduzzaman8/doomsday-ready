from django.core.management.base import BaseCommand
from django.db import transaction

from cinemas.models import Cinema
from movies.models import Movie

# (title, release year, runtime in minutes, titles to watch first)
MOVIES = [
    ("Iron Man", 2008, 126, []),
    ("Captain America: The First Avenger", 2011, 124, []),
    ("The Avengers", 2012, 143, ["Iron Man", "Captain America: The First Avenger"]),
    ("Captain America: Civil War", 2016, 147, ["The Avengers"]),
    ("Thor: Ragnarok", 2017, 130, []),
    ("Avengers: Infinity War", 2018, 149, ["Captain America: Civil War", "Thor: Ragnarok"]),
    ("Avengers: Endgame", 2019, 181, ["Avengers: Infinity War"]),
    # The real runtime is not known yet, so 150 is a placeholder.
    ("Avengers: Doomsday", 2026, 150, ["Avengers: Endgame"]),
]

CINEMAS = [
    ("Cinema Alpha", [1, 3, 4]),
    ("Cinema Bravo", [2, 5]),
    ("Cinema Charlie", [6, 9, 20]),
    ("Cinema Delta", [4, 6]),
]


class Command(BaseCommand):
    help = "Load the sample movies and cinemas into empty tables."

    @transaction.atomic
    def handle(self, *args, **options) -> None:
        self.seed_movies()
        self.seed_cinemas()

    def seed_movies(self) -> None:
        if Movie.objects.exists():
            self.stdout.write("Movies already seeded")
            return
        movies_by_title = {}
        for title, release_year, runtime_minutes, _ in MOVIES:
            movies_by_title[title] = Movie.objects.create(
                title=title, release_year=release_year, runtime_minutes=runtime_minutes
            )
        for title, _, _, prerequisite_titles in MOVIES:
            prerequisites = [movies_by_title[name] for name in prerequisite_titles]
            movies_by_title[title].prerequisites.set(prerequisites)
        self.stdout.write(f"Seeded {len(MOVIES)} movies")

    def seed_cinemas(self) -> None:
        if Cinema.objects.exists():
            self.stdout.write("Cinemas already seeded")
            return
        for name, bundle_sizes in CINEMAS:
            Cinema.objects.create(name=name, bundle_sizes=bundle_sizes)
        self.stdout.write(f"Seeded {len(CINEMAS)} cinemas")
