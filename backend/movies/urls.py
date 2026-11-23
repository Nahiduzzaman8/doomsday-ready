from django.urls import path

from movies.views import MovieDetailView, MovieListView

urlpatterns = [
    path("movies", MovieListView.as_view()),
    path("movies/<int:movie_id>", MovieDetailView.as_view()),
]
