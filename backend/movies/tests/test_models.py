from django.db import IntegrityError, transaction
from django.test import TestCase

from movies.models import Movie


def make_movie(**overrides) -> Movie:
    fields = {"title": "Iron Man", "release_year": 2008, "runtime_minutes": 126}
    fields.update(overrides)
    return Movie.objects.create(**fields)


class MovieConstraintTests(TestCase):
    def assert_rejected(self, constraint_name, **fields):
        # Each failing insert gets its own savepoint so the test transaction stays usable.
        with self.assertRaisesMessage(IntegrityError, constraint_name), transaction.atomic():
            make_movie(**fields)

    def test_title_is_unique_ignoring_case(self):
        make_movie(title="Iron Man")
        self.assert_rejected("unique_movie_title_ci", title="IRON man")

    def test_runtime_must_be_1_to_300(self):
        self.assert_rejected("movie_runtime_range", runtime_minutes=0)
        self.assert_rejected("movie_runtime_range", runtime_minutes=301)

    def test_runtime_limits_are_allowed(self):
        make_movie(title="Short", runtime_minutes=1)
        make_movie(title="Long", runtime_minutes=300)
        self.assertEqual(Movie.objects.count(), 2)

    def test_release_year_must_be_1900_to_2100(self):
        self.assert_rejected("movie_release_year_range", release_year=1899)
        self.assert_rejected("movie_release_year_range", release_year=2101)

    def test_release_year_limits_are_allowed(self):
        make_movie(title="Old", release_year=1900)
        make_movie(title="Future", release_year=2100)
        self.assertEqual(Movie.objects.count(), 2)


class MoviePrerequisiteTests(TestCase):
    def test_prerequisite_link_is_one_way(self):
        iron_man = make_movie(title="Iron Man")
        avengers = make_movie(title="The Avengers", release_year=2012, runtime_minutes=143)

        avengers.prerequisites.add(iron_man)

        self.assertEqual(list(avengers.prerequisites.all()), [iron_man])
        self.assertEqual(list(iron_man.prerequisites.all()), [])
        self.assertEqual(list(iron_man.required_for.all()), [avengers])


class MovieOrderingTests(TestCase):
    def test_default_order_is_release_year_then_title(self):
        make_movie(title="The Avengers", release_year=2012)
        make_movie(title="Iron Man 2", release_year=2010)
        make_movie(title="Captain America: The First Avenger", release_year=2011)
        make_movie(title="Thor", release_year=2011)

        titles = list(Movie.objects.values_list("title", flat=True))

        self.assertEqual(
            titles,
            ["Iron Man 2", "Captain America: The First Avenger", "Thor", "The Avengers"],
        )
