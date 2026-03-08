from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import MeProfileView, ProfileView, RegisterView, UserViewSet

router = DefaultRouter()
router.register(r"users", UserViewSet, basename="users")

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("profile/", ProfileView.as_view(), name="profile"),
    path("me/profile/", MeProfileView.as_view(), name="me-profile"),
]

urlpatterns += router.urls
