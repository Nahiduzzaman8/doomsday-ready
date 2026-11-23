from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from rest_framework.test import APITestCase

from movies.models import Movie
from movies.services import load_graph

CIRCULAR = {
    "error": {
        "code": "CIRCULAR_DEPENDENCY",
        "message": "This change would make a movie depend on itself.",
        "details": {},
    }
}
TITLE_TAKEN = {
    "error": {
        "code": "ALREADY_EXISTS",
        "message": "A movie with this title already exists.",
        "details": {},
    }
}
NOT_FOUND = {"error": {"code": "NOT_FOUND", "message": "Not found.", "details": {}}}
DOOMSDAY_ORDER = [
    "Iron Man",
    "Captain America: The First Avenger",
    "The Avengers",
    "Captain America: Civil War",
    "Thor: Ragnarok",
    "Avengers: Infinity War",
    "Avengers: Endgame",
]


def make_movie(title: str, release_year: int, runtime_minutes: int = 120, **extra) -> Movie:
    return Movie.objects.create(
        title=title, release_year=release_year, runtime_minutes=runtime_minutes, **extra
    )


def prerequisite_ids(movie: Movie) -> list[int]:
    return list(movie.prerequisites.values_list("id", flat=True))


class MovieApiTestCase(APITestCase):
    def post_movie(self, **overrides):
        body = {"title": "Iron Man", "release_year": 2008, "runtime_minutes": 126}
        body.update(overrides)
        return self.client.post("/api/movies", body, format="json")

    def patch_movie(self, movie: Movie, body: dict):
        return self.client.patch(f"/api/movies/{movie.id}", body, format="json")


class CreateMovieTests(MovieApiTestCase):
    def test_create_without_prerequisites_returns_movie_object(self):
        response = self.post_movie(title="  Iron Man  ")

        self.assertEqual(response.status_code, 201)
        movie = Movie.objects.get()
        self.assertEqual(
            response.json(),
            {
                "id": movie.id,
                "title": "Iron Man",
                "release_year": 2008,
                "runtime_minutes": 126,
                "watched": False,
                "prerequisites": [],
            },
        )

    def test_create_with_prerequisites_saves_them_sorted(self):
        thor = make_movie("Thor", 2011)
        iron_man = make_movie("Iron Man", 2008)
        captain = make_movie("Captain America: The First Avenger", 2011)

        response = self.post_movie(
            title="The Avengers",
            release_year=2012,
            watched=True,
            prerequisites=[thor.id, iron_man.id, captain.id],
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["prerequisites"], [iron_man.id, captain.id, thor.id])
        self.assertTrue(response.json()["watched"])
        avengers = Movie.objects.get(title="The Avengers")
        self.assertEqual(prerequisite_ids(avengers), [iron_man.id, captain.id, thor.id])

    def test_duplicate_prerequisite_ids_are_saved_once(self):
        iron_man = make_movie("Iron Man", 2008)

        response = self.post_movie(
            title="Iron Man 2", release_year=2010, prerequisites=[iron_man.id, iron_man.id]
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["prerequisites"], [iron_man.id])
        self.assertEqual(prerequisite_ids(Movie.objects.get(title="Iron Man 2")), [iron_man.id])

    def test_duplicate_title_in_any_case_is_rejected(self):
        make_movie("Iron Man", 2008)

        for title in ["Iron Man", "IRON man", "  iron man "]:
            with self.subTest(title=title):
                response = self.post_movie(title=title)
                self.assertEqual(response.status_code, 409)
                self.assertEqual(response.json(), TITLE_TAKEN)

        self.assertEqual(Movie.objects.count(), 1)


class MovieValidationTests(MovieApiTestCase):
    def assert_invalid(self, response, field: str):
        self.assertEqual(response.status_code, 400)
        error = response.json()["error"]
        self.assertEqual(error["code"], "VALIDATION_ERROR")
        self.assertEqual(error["message"], "Invalid input.")
        self.assertIn(field, error["details"])

    def test_bad_values_are_rejected(self):
        cases = [
            ("runtime_minutes", 0),
            ("runtime_minutes", 301),
            ("runtime_minutes", "126"),
            ("runtime_minutes", 2.5),
            ("runtime_minutes", True),
            ("release_year", 1899),
            ("release_year", 2101),
            ("release_year", "2008"),
            ("title", ""),
            ("title", "   "),
            ("title", "x" * 201),
            ("watched", "true"),
            ("watched", 1),
            ("prerequisites", "1"),
            ("prerequisites", ["1"]),
        ]
        for field, value in cases:
            with self.subTest(field=field, value=value):
                self.assert_invalid(self.post_movie(**{field: value}), field)

        self.assertEqual(Movie.objects.count(), 0)

    def test_missing_required_fields_are_rejected(self):
        response = self.client.post("/api/movies", {}, format="json")

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            set(response.json()["error"]["details"]),
            {"title", "release_year", "runtime_minutes"},
        )

    def test_bad_value_on_patch_is_rejected(self):
        movie = make_movie("Iron Man", 2008, 126)

        self.assert_invalid(self.patch_movie(movie, {"runtime_minutes": 301}), "runtime_minutes")

        movie.refresh_from_db()
        self.assertEqual(movie.runtime_minutes, 126)

    def test_unknown_prerequisite_id_is_listed_in_details(self):
        iron_man = make_movie("Iron Man", 2008)

        response = self.post_movie(title="Iron Man 2", prerequisites=[iron_man.id, 9999])

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json(),
            {
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Invalid input.",
                    "details": {"prerequisites": ["Unknown movie ids: 9999."]},
                }
            },
        )

    def test_unknown_fields_and_id_are_ignored(self):
        response = self.post_movie(id=500, rating=10)

        self.assertEqual(response.status_code, 201)
        self.assertNotEqual(response.json()["id"], 500)
        self.assertNotIn("rating", response.json())


class ReadMovieTests(MovieApiTestCase):
    def test_list_is_ordered_by_release_year_then_title(self):
        make_movie("The Avengers", 2012)
        make_movie("Thor", 2011)
        make_movie("Iron Man", 2008)
        make_movie("Captain America: The First Avenger", 2011)

        response = self.client.get("/api/movies")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [movie["title"] for movie in response.json()],
            ["Iron Man", "Captain America: The First Avenger", "Thor", "The Avengers"],
        )

    def test_list_is_empty_without_movies(self):
        response = self.client.get("/api/movies")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

    def test_get_one_movie(self):
        iron_man = make_movie("Iron Man", 2008, 126)
        avengers = make_movie("The Avengers", 2012, 143, watched=True)
        avengers.prerequisites.add(iron_man)

        response = self.client.get(f"/api/movies/{avengers.id}")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "id": avengers.id,
                "title": "The Avengers",
                "release_year": 2012,
                "runtime_minutes": 143,
                "watched": True,
                "prerequisites": [iron_man.id],
            },
        )

    def test_get_unknown_id_is_not_found(self):
        response = self.client.get("/api/movies/9999")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), NOT_FOUND)

    def test_patch_unknown_id_is_not_found(self):
        response = self.client.patch("/api/movies/9999", {"watched": True}, format="json")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), NOT_FOUND)

    def test_wrong_method_is_rejected(self):
        response = self.client.delete("/api/movies")

        self.assertEqual(response.status_code, 405)
        self.assertEqual(response.json()["error"]["code"], "METHOD_NOT_ALLOWED")


class UpdateMovieTests(MovieApiTestCase):
    def setUp(self):
        self.iron_man = make_movie("Iron Man", 2008, 126)
        self.captain = make_movie("Captain America: The First Avenger", 2011, 124)
        self.avengers = make_movie("The Avengers", 2012, 143)
        self.avengers.prerequisites.set([self.iron_man, self.captain])

    def test_watched_only_patch_keeps_other_fields(self):
        response = self.patch_movie(self.avengers, {"watched": True})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "id": self.avengers.id,
                "title": "The Avengers",
                "release_year": 2012,
                "runtime_minutes": 143,
                "watched": True,
                "prerequisites": [self.iron_man.id, self.captain.id],
            },
        )
        self.avengers.refresh_from_db()
        self.assertTrue(self.avengers.watched)

    def test_watched_only_patch_does_not_lock_movies(self):
        with CaptureQueriesContext(connection) as queries:
            self.patch_movie(self.avengers, {"watched": True})

        self.assertFalse(any("FOR UPDATE" in query["sql"] for query in queries))

    def test_prerequisites_patch_locks_movies(self):
        with CaptureQueriesContext(connection) as queries:
            self.patch_movie(self.avengers, {"prerequisites": [self.iron_man.id]})

        self.assertTrue(any("FOR UPDATE" in query["sql"] for query in queries))

    def test_patch_prerequisites_replaces_the_list(self):
        response = self.patch_movie(self.avengers, {"prerequisites": [self.captain.id]})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["prerequisites"], [self.captain.id])
        self.assertEqual(prerequisite_ids(self.avengers), [self.captain.id])

    def test_patch_empty_prerequisites_clears_the_list(self):
        response = self.patch_movie(self.avengers, {"prerequisites": []})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["prerequisites"], [])
        self.assertEqual(prerequisite_ids(self.avengers), [])

    def test_patch_without_prerequisites_keeps_them(self):
        response = self.patch_movie(self.avengers, {"runtime_minutes": 150})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["runtime_minutes"], 150)
        self.assertEqual(response.json()["prerequisites"], [self.iron_man.id, self.captain.id])
        self.assertEqual(prerequisite_ids(self.avengers), [self.iron_man.id, self.captain.id])

    def test_patch_duplicate_prerequisite_ids_are_saved_once(self):
        response = self.patch_movie(
            self.avengers, {"prerequisites": [self.iron_man.id, self.iron_man.id]}
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(prerequisite_ids(self.avengers), [self.iron_man.id])

    def test_patch_to_another_movies_title_in_any_case_is_rejected(self):
        for title in ["Iron Man", "iron MAN"]:
            with self.subTest(title=title):
                response = self.patch_movie(self.avengers, {"title": title})
                self.assertEqual(response.status_code, 409)
                self.assertEqual(response.json(), TITLE_TAKEN)

        self.avengers.refresh_from_db()
        self.assertEqual(self.avengers.title, "The Avengers")

    def test_patch_with_own_title_is_not_a_duplicate(self):
        response = self.patch_movie(self.avengers, {"title": "The Avengers", "watched": True})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["title"], "The Avengers")

    def test_patch_unknown_prerequisite_keeps_old_list(self):
        response = self.patch_movie(self.avengers, {"prerequisites": [9999]})

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json()["error"]["details"], {"prerequisites": ["Unknown movie ids: 9999."]}
        )
        self.assertEqual(prerequisite_ids(self.avengers), [self.iron_man.id, self.captain.id])


class CircularDependencyTests(MovieApiTestCase):
    def setUp(self):
        # The brief's chain: Iron Man <- The Avengers <- Civil War <- Infinity War <- Endgame.
        self.iron_man = make_movie("Iron Man", 2008, 126)
        self.captain = make_movie("Captain America: The First Avenger", 2011, 124)
        self.avengers = make_movie("The Avengers", 2012, 143)
        self.civil_war = make_movie("Captain America: Civil War", 2016, 147)
        self.infinity_war = make_movie("Avengers: Infinity War", 2018, 149)
        self.endgame = make_movie("Avengers: Endgame", 2019, 181)
        self.avengers.prerequisites.set([self.iron_man, self.captain])
        self.civil_war.prerequisites.set([self.avengers])
        self.infinity_war.prerequisites.set([self.civil_war])
        self.endgame.prerequisites.set([self.infinity_war])

    def test_movie_as_its_own_prerequisite(self):
        response = self.patch_movie(
            self.avengers, {"prerequisites": [self.iron_man.id, self.avengers.id]}
        )

        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json(), CIRCULAR)
        self.assertEqual(prerequisite_ids(self.avengers), [self.iron_man.id, self.captain.id])

    def test_brief_example_endgame_before_iron_man(self):
        response = self.patch_movie(self.iron_man, {"prerequisites": [self.endgame.id]})

        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json(), CIRCULAR)
        self.assertEqual(prerequisite_ids(self.iron_man), [])

    def test_cycle_keeps_existing_prerequisites(self):
        response = self.patch_movie(
            self.avengers, {"prerequisites": [self.captain.id, self.infinity_war.id]}
        )

        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json(), CIRCULAR)
        self.assertEqual(prerequisite_ids(self.avengers), [self.iron_man.id, self.captain.id])

    def test_cycle_also_rolls_back_other_fields(self):
        response = self.patch_movie(
            self.iron_man,
            {"watched": True, "runtime_minutes": 200, "prerequisites": [self.endgame.id]},
        )

        self.assertEqual(response.status_code, 409)
        self.iron_man.refresh_from_db()
        self.assertFalse(self.iron_man.watched)
        self.assertEqual(self.iron_man.runtime_minutes, 126)
        self.assertEqual(prerequisite_ids(self.iron_man), [])

    def test_duplicate_title_keeps_existing_prerequisites(self):
        response = self.patch_movie(
            self.avengers, {"title": "Iron Man", "prerequisites": [self.captain.id]}
        )

        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json(), TITLE_TAKEN)
        self.assertEqual(prerequisite_ids(self.avengers), [self.iron_man.id, self.captain.id])

    def test_link_that_does_not_close_a_loop_is_allowed(self):
        response = self.patch_movie(
            self.endgame, {"prerequisites": [self.infinity_war.id, self.iron_man.id]}
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["prerequisites"], [self.iron_man.id, self.infinity_war.id])


class LoadGraphTests(TestCase):
    def test_every_movie_is_a_key_with_sorted_prerequisites(self):
        avengers = make_movie("The Avengers", 2012)
        thor = make_movie("Thor", 2011)
        iron_man = make_movie("Iron Man", 2008)
        captain = make_movie("Captain America: The First Avenger", 2011)
        ragnarok = make_movie("Thor: Ragnarok", 2017)
        avengers.prerequisites.set([thor, iron_man, captain])

        self.assertEqual(
            load_graph(),
            {
                avengers.id: [iron_man.id, captain.id, thor.id],
                thor.id: [],
                iron_man.id: [],
                captain.id: [],
                ragnarok.id: [],
            },
        )

    def test_empty_database_gives_empty_graph(self):
        self.assertEqual(load_graph(), {})


class RewatchOrderTests(APITestCase):
    def setUp(self):
        iron_man = make_movie("Iron Man", 2008, 126)
        first_avenger = make_movie("Captain America: The First Avenger", 2011, 124)
        avengers = make_movie("The Avengers", 2012, 143)
        civil_war = make_movie("Captain America: Civil War", 2016, 147)
        ragnarok = make_movie("Thor: Ragnarok", 2017, 130)
        infinity_war = make_movie("Avengers: Infinity War", 2018, 149)
        endgame = make_movie("Avengers: Endgame", 2019, 181)
        doomsday = make_movie("Avengers: Doomsday", 2026, 150)

        avengers.prerequisites.set([iron_man, first_avenger])
        civil_war.prerequisites.set([avengers])
        infinity_war.prerequisites.set([civil_war, ragnarok])
        endgame.prerequisites.set([infinity_war])
        doomsday.prerequisites.set([endgame])
        self.movies = {movie.title: movie for movie in Movie.objects.all()}

    def get_plan(self, title: str) -> dict:
        response = self.client.get(f"/api/movies/{self.movies[title].id}/rewatch-order")
        self.assertEqual(response.status_code, 200)
        return response.json()

    def titles(self, plan: dict) -> list[str]:
        return [movie["title"] for movie in plan["movies"]]

    def test_brief_example_doomsday(self):
        plan = self.get_plan("Avengers: Doomsday")

        self.assertEqual(self.titles(plan), DOOMSDAY_ORDER)
        position = {movie["id"]: index for index, movie in enumerate(plan["movies"])}
        for movie in plan["movies"]:
            for prerequisite_id in movie["prerequisites"]:
                self.assertLess(position[prerequisite_id], position[movie["id"]])

    def test_brief_example_civil_war(self):
        titles = self.titles(self.get_plan("Captain America: Civil War"))

        self.assertCountEqual(titles[:2], ["Iron Man", "Captain America: The First Avenger"])
        self.assertEqual(titles[2:], ["The Avengers"])

    def test_brief_example_ragnarok_has_nothing_to_watch(self):
        ragnarok = self.movies["Thor: Ragnarok"]

        self.assertEqual(
            self.get_plan("Thor: Ragnarok"),
            {
                "target": {"id": ragnarok.id, "title": "Thor: Ragnarok"},
                "movies": [],
                "total_count": 0,
                "watched_count": 0,
                "unwatched_runtime_minutes": 0,
            },
        )

    def test_target_is_never_in_its_own_list(self):
        for title, target in self.movies.items():
            with self.subTest(title=title):
                plan = self.get_plan(title)
                self.assertEqual(plan["target"], {"id": target.id, "title": title})
                self.assertNotIn(target.id, [movie["id"] for movie in plan["movies"]])

    def test_watched_movies_are_counted_and_left_out_of_runtime(self):
        watched = DOOMSDAY_ORDER[:4]
        Movie.objects.filter(title__in=watched).update(watched=True)

        plan = self.get_plan("Avengers: Doomsday")

        self.assertEqual(plan["total_count"], 7)
        self.assertEqual(plan["watched_count"], 4)
        self.assertEqual(plan["unwatched_runtime_minutes"], 460)
        self.assertEqual(self.titles(plan), DOOMSDAY_ORDER)
        self.assertEqual(
            plan["movies"][0],
            {
                "id": self.movies["Iron Man"].id,
                "title": "Iron Man",
                "release_year": 2008,
                "runtime_minutes": 126,
                "watched": True,
                "prerequisites": [],
            },
        )

    def test_unknown_id_is_not_found(self):
        response = self.client.get("/api/movies/999999/rewatch-order")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), NOT_FOUND)
