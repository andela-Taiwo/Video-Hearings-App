from rest_framework import viewsets
from rest_framework.permissions import AllowAny
from .models import Case
from .serializers import CaseListSerializer


class CaseViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Case.objects.all()
    serializer_class = CaseListSerializer
    permission_classes = [AllowAny]
