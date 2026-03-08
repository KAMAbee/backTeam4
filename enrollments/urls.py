from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MyEnrollmentsViewSet, AdminEnrollmentViewSet

router = DefaultRouter()
router.register(r'my', MyEnrollmentsViewSet, basename='my-enrollments')
router.register(r'manage', AdminEnrollmentViewSet, basename='admin-enrollments')

urlpatterns = [
    path(
        "session/<uuid:session_id>/participants/",
        AdminEnrollmentViewSet.as_view({"get": "session_participants", "patch": "session_participants"}),
        name="admin-enrollments-session-participants",
    ),
    path('', include(router.urls)),
]
