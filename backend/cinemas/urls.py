from django.urls import path

from cinemas.views import BookingQuoteView, CinemaListView

urlpatterns = [
    path("cinemas", CinemaListView.as_view()),
    path("cinemas/<int:cinema_id>/booking", BookingQuoteView.as_view()),
]
