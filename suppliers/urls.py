from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import ContractViewSet, SupplierViewSet, budget_summary

router = DefaultRouter()
router.register(r"suppliers", SupplierViewSet, basename="supplier")
router.register(r"contracts", ContractViewSet, basename="contract")

urlpatterns = [
    *router.urls,
    path("budget-summary/", budget_summary, name="budget-summary"),
]