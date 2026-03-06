from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CourtroomViewSet

router = DefaultRouter()
router.register(r"courtrooms", CourtroomViewSet, basename="courtroom")

urlpatterns = [
    path("", include(router.urls)),
]
