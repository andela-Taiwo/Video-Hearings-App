from rest_framework import viewsets
from rest_framework.permissions import AllowAny
from .models import Courtroom
from .serializers import CourtroomSerializer


class CourtroomViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Courtroom.objects.all()
    serializer_class = CourtroomSerializer
    permission_classes = [AllowAny]
