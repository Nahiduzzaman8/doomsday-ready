from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("movies.urls")),
    path("api/", include("cinemas.urls")),
]

handler404 = "config.views.not_found"
handler500 = "config.views.server_error"
