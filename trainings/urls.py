from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TrainingViewSet, TrainingSessionViewSet

router = DefaultRouter()
router.register(r'list', TrainingViewSet)
router.register(r'sessions', TrainingSessionViewSet)

urlpatterns = [
    path('', include(router.urls)),
]