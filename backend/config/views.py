from django.http import JsonResponse

from config.exceptions import error_body


def not_found(request, exception):
    return JsonResponse(error_body("NOT_FOUND", "Not found."), status=404)


def server_error(request):
    return JsonResponse(error_body("INTERNAL_ERROR", "Something went wrong."), status=500)
