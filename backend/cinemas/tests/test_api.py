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
