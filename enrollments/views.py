from rest_framework import viewsets, mixins, permissions
from .models import TrainingEnrollment
from .serializers import TrainingEnrollmentSerializer, AdminEnrollmentUpdateSerializer
from accounts.permissions import IsAdminRole

class MyEnrollmentsViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TrainingEnrollmentSerializer
    def get_queryset(self):
        return TrainingEnrollment.objects.filter(employee=self.request.user)

class AdminEnrollmentViewSet(mixins.UpdateModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = TrainingEnrollment.objects.all()
    serializer_class = AdminEnrollmentUpdateSerializer
    permission_classes = [IsAdminRole]