from io import StringIO

from django.core.management import call_command
from rest_framework.test import APITestCase

from cinemas.models import Cinema
from movies.models import Movie
from movies.tests.test_api import DOOMSDAY_ORDER

EXPECTED_MOVIES = {
    "Iron Man": (2008, 126),
    "Captain America: The First Avenger": (2011, 124),
    "The Avengers": (2012, 143),
    "Captain America: Civil War": (2016, 147),
    "Thor: Ragnarok": (2017, 130),
    "Avengers: Infinity War": (2018, 149),
    "Avengers: Endgame": (2019, 181),
    "Avengers: Doomsday": (2026, 150),
}
EXPECTED_PREREQUISITES = {
    "Iron Man": set(),
    "Captain America: The First Avenger": set(),
    "The Avengers": {"Iron Man", "Captain America: The First Avenger"},
    "Captain America: Civil War": {"The Avengers"},
    "Thor: Ragnarok": set(),
    "Avengers: Infinity War": {"Captain America: Civil War", "Thor: Ragnarok"},
    "Avengers: Endgame": {"Avengers: Infinity War"},
    "Avengers: Doomsday": {"Avengers: Endgame"},
}
EXPECTED_CINEMAS = {
    "Cinema Alpha": [1, 3, 4],
    "Cinema Bravo": [2, 5],
    "Cinema Charlie": [6, 9, 20],
    "Cinema Delta": [4, 6],
}


def run_seed() -> str:
    output = StringIO()
    call_command("seed", stdout=output)
    return output.getvalue()


class SeedTests(APITestCase):
    def test_empty_database_gets_sample_movies_and_cinemas(self):
        run_seed()

        movies = {
            movie.title: (movie.release_year, movie.runtime_minutes)
            for movie in Movie.objects.all()
        }
        self.assertEqual(movies, EXPECTED_MOVIES)
        self.assertFalse(Movie.objects.filter(watched=True).exists())
        cinemas = {cinema.name: cinema.bundle_sizes for cinema in Cinema.objects.all()}
        self.assertEqual(cinemas, EXPECTED_CINEMAS)

    def test_prerequisites_match_the_spec(self):
        run_seed()

        prerequisites = {
            movie.title: {prerequisite.title for prerequisite in movie.prerequisites.all()}
            for movie in Movie.objects.prefetch_related("prerequisites")
        }
        self.assertEqual(prerequisites, EXPECTED_PREREQUISITES)

    def test_running_twice_does_not_add_rows(self):
        run_seed()
        output = run_seed()

        self.assertEqual(Movie.objects.count(), 8)
        self.assertEqual(Cinema.objects.count(), 4)
        self.assertIn("Movies already seeded", output)
        self.assertIn("Cinemas already seeded", output)

    def test_running_again_keeps_watched_flag(self):
        run_seed()
        Movie.objects.filter(title="Iron Man").update(watched=True)

        run_seed()

        self.assertTrue(Movie.objects.get(title="Iron Man").watched)

    def test_tables_are_checked_separately(self):
        Cinema.objects.create(name="My Cinema", bundle_sizes=[2])

        run_seed()

        self.assertEqual(Movie.objects.count(), 8)
        self.assertEqual(list(Cinema.objects.values_list("name", flat=True)), ["My Cinema"])

    def test_doomsday_rewatch_order_after_seeding(self):
        run_seed()
        doomsday = Movie.objects.get(title="Avengers: Doomsday")

        response = self.client.get(f"/api/movies/{doomsday.id}/rewatch-order")

        self.assertEqual(response.status_code, 200)
        titles = [movie["title"] for movie in response.json()["movies"]]
        self.assertEqual(titles, DOOMSDAY_ORDER)
        self.assertEqual(response.json()["total_count"], 7)
