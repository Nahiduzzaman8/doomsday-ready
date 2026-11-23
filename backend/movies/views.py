from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from movies import services
from movies.serializers import MovieInputSerializer, MovieSerializer, RewatchPlanSerializer


class MovieListView(APIView):
    def get(self, request):
        movies = services.list_movies()
        return Response(MovieSerializer(movies, many=True).data)

    def post(self, request):
        serializer = MovieInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        movie = services.create_movie(serializer.validated_data)
        return Response(MovieSerializer(movie).data, status=status.HTTP_201_CREATED)


class MovieDetailView(APIView):
    def get(self, request, movie_id):
        movie = services.get_movie(movie_id)
        return Response(MovieSerializer(movie).data)

    def patch(self, request, movie_id):
        movie = services.get_movie(movie_id)
        serializer = MovieInputSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        movie = services.update_movie(movie, serializer.validated_data)
        return Response(MovieSerializer(movie).data)


class RewatchOrderView(APIView):
    def get(self, request, movie_id):
        movie = services.get_movie(movie_id)
        plan = services.get_rewatch_plan(movie)
        return Response(RewatchPlanSerializer(plan).data)
