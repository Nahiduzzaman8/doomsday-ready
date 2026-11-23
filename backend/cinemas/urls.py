from django.urls import path

from cinemas.views import CinemaListView

urlpatterns = [
    path("cinemas", CinemaListView.as_view()),
]
