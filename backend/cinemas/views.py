from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from cinemas import services
from cinemas.serializers import CinemaInputSerializer, CinemaSerializer


class CinemaListView(APIView):
    def get(self, request):
        cinemas = services.list_cinemas()
        return Response(CinemaSerializer(cinemas, many=True).data)

    def post(self, request):
        serializer = CinemaInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        cinema = services.create_cinema(serializer.validated_data)
        return Response(CinemaSerializer(cinema).data, status=status.HTTP_201_CREATED)
