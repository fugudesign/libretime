from django.conf import settings
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView


class StationsView(APIView):
    """Return the list of stations defined in config."""

    def get(self, request: Request) -> Response:
        data = [
            {"id": s.id, "name": s.name}
            for s in settings.CONFIG.stations
        ]
        return Response(data)
