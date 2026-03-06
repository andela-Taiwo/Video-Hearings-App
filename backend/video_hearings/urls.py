from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import hearings

router = DefaultRouter()
router.register(r"", hearings.HearingViewSet, basename="hearing")

# router_v1 = DefaultRouter()
# router_v1.register(r"hearings", hearings.HearingViewSet, basename="hearing_v1")

async_urls = [
    # path('upload/<str:hearing_id>/', view.AsyncDocumentUploadView.as_view(), name='upload'),
    # path('upload/<str:upload_id>/', views.UploadStatusView.as_view(), name='upload-status'),
]

urlpatterns = [
    path("", include(router.urls)),
    # path("", include(async_urls)),
]
