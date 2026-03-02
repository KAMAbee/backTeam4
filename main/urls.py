from django.urls import include, path

urlpatterns = [
    # `main` acts as an API aggregator for domain apps.
    path("", include("suppliers.urls")),
]