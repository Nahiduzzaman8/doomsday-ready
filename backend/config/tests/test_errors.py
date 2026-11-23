from django.http import Http404
from django.test import override_settings
from django.urls import include, path
from rest_framework import serializers
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.test import APITestCase
from rest_framework.views import APIView

from config.exceptions import AlreadyExists, CircularDependency
from config.urls import handler404, handler500  # noqa: F401 (used by the test URLconf)


class CountSerializer(serializers.Serializer):
    count = serializers.IntegerField(max_value=10)


class EchoView(APIView):
    def post(self, request):
        serializer = CountSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data)


ERRORS = {
    "not-found": NotFound(),
    "http404": Http404(),
    "circular": CircularDependency(),
    "exists": AlreadyExists("A movie with this title already exists."),
    "crash": RuntimeError("secret internals"),
}


class RaiseView(APIView):
    def get(self, request, name):
        raise ERRORS[name]


def plain_django_crash(request):
    raise RuntimeError("secret internals")


urlpatterns = [
    path("api/test/echo", EchoView.as_view()),
    path("api/test/raise/<str:name>", RaiseView.as_view()),
    path("api/test/plain-crash", plain_django_crash),
    path("", include("config.urls")),
]


@override_settings(ROOT_URLCONF="config.tests.test_errors")
class ErrorShapeTests(APITestCase):
    def assert_error(self, response, status, code, message, details=None):
        self.assertEqual(response.status_code, status)
        self.assertEqual(response["Content-Type"], "application/json")
        self.assertEqual(
            response.json(),
            {"error": {"code": code, "message": message, "details": details or {}}},
        )

    def test_validation_error_lists_field_errors(self):
        response = self.client.post("/api/test/echo", {"count": 11}, format="json")
        self.assert_error(
            response, 400, "VALIDATION_ERROR", "Invalid input.",
            {"count": ["Ensure this value is less than or equal to 10."]},
        )

    def test_missing_field_is_validation_error(self):
        response = self.client.post("/api/test/echo", {}, format="json")
        self.assert_error(
            response, 400, "VALIDATION_ERROR", "Invalid input.",
            {"count": ["This field is required."]},
        )

    def test_broken_json_is_validation_error(self):
        response = self.client.post(
            "/api/test/echo", data="{broken", content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)
        error = response.json()["error"]
        self.assertEqual(error["code"], "VALIDATION_ERROR")
        self.assertTrue(error["message"].startswith("JSON parse error"))
        self.assertEqual(error["details"], {})

    def test_drf_not_found(self):
        response = self.client.get("/api/test/raise/not-found")
        self.assert_error(response, 404, "NOT_FOUND", "Not found.")

    def test_django_http404(self):
        response = self.client.get("/api/test/raise/http404")
        self.assert_error(response, 404, "NOT_FOUND", "Not found.")

    def test_unknown_url_returns_json_404(self):
        response = self.client.get("/api/nope")
        self.assert_error(response, 404, "NOT_FOUND", "Not found.")

    def test_wrong_method(self):
        response = self.client.get("/api/test/echo")
        self.assert_error(response, 405, "METHOD_NOT_ALLOWED", "Method not allowed.")
        self.assertEqual(response["Allow"], "POST, OPTIONS")

    def test_circular_dependency(self):
        response = self.client.get("/api/test/raise/circular")
        self.assert_error(
            response, 409, "CIRCULAR_DEPENDENCY",
            "This change would make a movie depend on itself.",
        )

    def test_already_exists(self):
        response = self.client.get("/api/test/raise/exists")
        self.assert_error(
            response, 409, "ALREADY_EXISTS", "A movie with this title already exists."
        )

    def test_unexpected_exception_hides_details(self):
        with self.assertLogs("config.exceptions", level="ERROR"):
            response = self.client.get("/api/test/raise/crash")
        self.assert_error(response, 500, "INTERNAL_ERROR", "Something went wrong.")
        self.assertNotIn("secret internals", response.content.decode())
        self.assertNotIn("Traceback", response.content.decode())

    def test_crash_outside_drf_returns_json_500(self):
        self.client.raise_request_exception = False
        with self.assertLogs("django.request", level="ERROR"):
            response = self.client.get("/api/test/plain-crash")
        self.assert_error(response, 500, "INTERNAL_ERROR", "Something went wrong.")
        self.assertNotIn("secret internals", response.content.decode())
