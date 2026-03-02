from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import ContractViewSet, budget_summary

router = DefaultRouter()
router.register(r"contracts", ContractViewSet, basename="contract")

urlpatterns = [
    path("", include(router.urls)),
    path("budget-summary/", budget_summary, name="budget-summary"),
]