from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError


class BaseHearingViewSet(viewsets.ModelViewSet):
    """
    Base ViewSet with common functionality for all hearing-related views
    """

    service_class = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.service = self.service_class() if self.service_class else None

    def handle_service_error(self, e):
        """Centralized error handling"""
        if isinstance(e, ValidationError):
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(
            {"error": f"An unexpected error occurred: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
