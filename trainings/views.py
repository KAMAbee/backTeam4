from rest_framework import viewsets
from .models import Training, TrainingSession
from .serializers import TrainingSerializer, TrainingSessionSerializer

class TrainingViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Training.objects.all()
    serializer_class = TrainingSerializer

class TrainingSessionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = TrainingSession.objects.all()
    serializer_class = TrainingSessionSerializer