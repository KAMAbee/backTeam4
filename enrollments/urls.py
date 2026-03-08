from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MyEnrollmentsViewSet, AdminEnrollmentViewSet

router = DefaultRouter()
router.register(r'my', MyEnrollmentsViewSet, basename='my-enrollments')
router.register(r'manage', AdminEnrollmentViewSet, basename='admin-enrollments')

urlpatterns = [
    path('', include(router.urls)),
]