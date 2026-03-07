from rest_framework import viewsets
from rest_framework.permissions import AllowAny
from .models import Courtroom
from .serializers import CourtroomSerializer


class CourtroomViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Courtroom.objects.all().order_by("name", "id")
    serializer_class = CourtroomSerializer
    permission_classes = [AllowAny]
