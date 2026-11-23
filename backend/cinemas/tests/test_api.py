from rest_framework.test import APITestCase

from cinemas.models import Cinema

NAME_TAKEN = {
    "error": {
        "code": "ALREADY_EXISTS",
        "message": "A cinema with this name already exists.",
        "details": {},
    }
}


class CinemaApiTestCase(APITestCase):
    def post_cinema(self, **overrides):
        body = {"name": "Cinema Bravo", "bundle_sizes": [2, 5]}
        body.update(overrides)
        return self.client.post("/api/cinemas", body, format="json")

    def assert_validation_error(self, response, field: str):
        self.assertEqual(response.status_code, 400)
        error = response.json()["error"]
        self.assertEqual(error["code"], "VALIDATION_ERROR")
        self.assertEqual(error["message"], "Invalid input.")
        self.assertIn(field, error["details"])


class CreateCinemaTests(CinemaApiTestCase):
    def test_create_returns_cinema_with_sorted_bundle_sizes(self):
        response = self.post_cinema(name="  Cinema Bravo  ", bundle_sizes=[5, 2])

        self.assertEqual(response.status_code, 201)
        cinema = Cinema.objects.get()
        self.assertEqual(
            response.json(), {"id": cinema.id, "name": "Cinema Bravo", "bundle_sizes": [2, 5]}
        )
        self.assertEqual(cinema.bundle_sizes, [2, 5])

    def test_duplicate_name_in_any_case_is_rejected(self):
        Cinema.objects.create(name="Cinema Bravo", bundle_sizes=[2, 5])

        for name in ["Cinema Bravo", "cinema BRAVO"]:
            with self.subTest(name=name):
                response = self.post_cinema(name=name)
                self.assertEqual(response.status_code, 409)
                self.assertEqual(response.json(), NAME_TAKEN)
        self.assertEqual(Cinema.objects.count(), 1)


class CinemaValidationTests(CinemaApiTestCase):
    def test_bad_bundle_sizes_are_rejected(self):
        bad_values = {
            "empty list": [],
            "eleven sizes": list(range(1, 12)),
            "zero": [0],
            "above 500": [501],
            "duplicates": [2, 2],
            "string number": ["2"],
        }
        for label, bundle_sizes in bad_values.items():
            with self.subTest(label):
                response = self.post_cinema(bundle_sizes=bundle_sizes)
                self.assert_validation_error(response, "bundle_sizes")
        self.assertFalse(Cinema.objects.exists())

    def test_missing_bundle_sizes_is_rejected(self):
        response = self.client.post("/api/cinemas", {"name": "Cinema Bravo"}, format="json")

        self.assert_validation_error(response, "bundle_sizes")

    def test_empty_name_is_rejected(self):
        for name in ["", "   "]:
            with self.subTest(name=name):
                response = self.post_cinema(name=name)
                self.assert_validation_error(response, "name")
        self.assertFalse(Cinema.objects.exists())

    def test_ten_sizes_at_the_limits_are_accepted(self):
        bundle_sizes = [500, 1, 2, 3, 4, 5, 6, 7, 8, 9]

        response = self.post_cinema(bundle_sizes=bundle_sizes)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["bundle_sizes"], sorted(bundle_sizes))


class ListCinemaTests(CinemaApiTestCase):
    def test_list_is_ordered_by_name(self):
        delta = Cinema.objects.create(name="Cinema Delta", bundle_sizes=[4, 6])
        alpha = Cinema.objects.create(name="Cinema Alpha", bundle_sizes=[1, 3, 4])

        response = self.client.get("/api/cinemas")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            [
                {"id": alpha.id, "name": "Cinema Alpha", "bundle_sizes": [1, 3, 4]},
                {"id": delta.id, "name": "Cinema Delta", "bundle_sizes": [4, 6]},
            ],
        )

    def test_list_is_empty_without_cinemas(self):
        response = self.client.get("/api/cinemas")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])


class BookingQuoteTests(APITestCase):
    def get_quote(self, cinema: Cinema, group_size: str):
        return self.client.get(f"/api/cinemas/{cinema.id}/booking", {"groupSize": group_size})

    def assert_possible(self, bundle_sizes: list[int], group_size: int, total: int, bundles: list):
        cinema = Cinema.objects.create(name="Cinema Test", bundle_sizes=bundle_sizes)

        response = self.get_quote(cinema, str(group_size))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "cinema": {"id": cinema.id, "name": "Cinema Test"},
                "group_size": group_size,
                "possible": True,
                "total_bundles": total,
                "bundles": [{"size": size, "count": count} for size, count in bundles],
            },
        )

    def test_brief_example_1_3_4_for_6(self):
        self.assert_possible([1, 3, 4], 6, total=2, bundles=[(3, 2)])

    def test_brief_example_2_5_for_11(self):
        self.assert_possible([2, 5], 11, total=4, bundles=[(5, 1), (2, 3)])

    def test_brief_example_6_9_20_for_44(self):
        self.assert_possible([6, 9, 20], 44, total=4, bundles=[(20, 1), (9, 2), (6, 1)])

    def test_brief_example_4_6_for_7_is_not_possible(self):
        cinema = Cinema.objects.create(name="Cinema Delta", bundle_sizes=[4, 6])

        response = self.get_quote(cinema, "7")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "cinema": {"id": cinema.id, "name": "Cinema Delta"},
                "group_size": 7,
                "possible": False,
                "total_bundles": None,
                "bundles": [],
                "message": "No combination of bundles adds up to exactly 7 seats.",
            },
        )

    def test_smallest_group_size_is_accepted(self):
        self.assert_possible([1, 3, 4], 1, total=1, bundles=[(1, 1)])

    def test_largest_group_size_is_accepted(self):
        self.assert_possible([2, 5], 10_000, total=2000, bundles=[(5, 2000)])


class BookingQuoteErrorTests(APITestCase):
    def test_bad_group_size_is_rejected(self):
        cinema = Cinema.objects.create(name="Cinema Bravo", bundle_sizes=[2, 5])
        url = f"/api/cinemas/{cinema.id}/booking"
        bad_queries = {
            "missing": {},
            "empty": {"groupSize": ""},
            "letters": {"groupSize": "abc"},
            "decimal": {"groupSize": "2.5"},
            "decimal with zero": {"groupSize": "11.0"},
            "spaces": {"groupSize": " 11 "},
            "negative": {"groupSize": "-1"},
            "zero": {"groupSize": "0"},
            "above 10000": {"groupSize": "10001"},
        }
        for label, query in bad_queries.items():
            with self.subTest(label):
                response = self.client.get(url, query)
                self.assertEqual(response.status_code, 400)
                error = response.json()["error"]
                self.assertEqual(error["code"], "VALIDATION_ERROR")
                self.assertEqual(error["message"], "Invalid input.")
                self.assertIn("groupSize", error["details"])

    def test_unknown_cinema_is_not_found(self):
        response = self.client.get("/api/cinemas/999/booking", {"groupSize": "6"})

        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.json(),
            {"error": {"code": "NOT_FOUND", "message": "Not found.", "details": {}}},
        )
