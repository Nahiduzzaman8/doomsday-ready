import logging

from django.http import Http404
from rest_framework import status
from rest_framework.exceptions import (
    APIException,
    MethodNotAllowed,
    NotFound,
    ParseError,
    ValidationError,
)
from rest_framework.response import Response
from rest_framework.settings import api_settings
from rest_framework.views import exception_handler

logger = logging.getLogger(__name__)


class CircularDependency(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_code = "CIRCULAR_DEPENDENCY"
    default_detail = "This change would make a movie depend on itself."


class AlreadyExists(APIException):
    """Callers pass the specific message, such as "A cinema with this name already exists."""

    status_code = status.HTTP_409_CONFLICT
    default_code = "ALREADY_EXISTS"
    default_detail = "This item already exists."


def error_body(code: str, message: str, details: dict | None = None) -> dict:
    return {"error": {"code": code, "message": message, "details": details or {}}}


def api_exception_handler(exc, context):
    # DRF converts Http404 internally but still hands us the original exception.
    if isinstance(exc, Http404):
        exc = NotFound()

    response = exception_handler(exc, context)
    if response is None:
        logger.error("Unhandled exception", exc_info=exc)
        return Response(
            error_body("INTERNAL_ERROR", "Something went wrong."),
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    # Reuse DRF's response so its status code and headers (such as Allow on 405) are kept.
    response.data = error_body(*_describe(exc, response.data))
    return response


def _describe(exc: APIException, data) -> tuple[str, str, dict]:
    if isinstance(exc, ValidationError):
        return "VALIDATION_ERROR", "Invalid input.", _field_errors(data)
    if isinstance(exc, ParseError):
        return "VALIDATION_ERROR", str(exc.detail), {}
    if isinstance(exc, NotFound):
        return "NOT_FOUND", "Not found.", {}
    if isinstance(exc, MethodNotAllowed):
        return "METHOD_NOT_ALLOWED", "Method not allowed.", {}
    return exc.default_code.upper(), str(exc.detail), {}


def _field_errors(data) -> dict:
    if isinstance(data, dict):
        return data
    return {api_settings.NON_FIELD_ERRORS_KEY: data}
