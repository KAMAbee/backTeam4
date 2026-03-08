from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TrainingRequestViewSet

router = DefaultRouter()
router.register(r"", TrainingRequestViewSet, basename="training-request")

urlpatterns = [
    path("", include(router.urls)),
]
