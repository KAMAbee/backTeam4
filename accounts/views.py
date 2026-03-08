from django.db.models import Q
from drf_spectacular.utils import extend_schema
from rest_framework import generics, viewsets
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated

from enrollments.models import TrainingEnrollment
from .models import User
from .serializers import (
    MeProfileCertificateSerializer,
    MeProfileResponseSerializer,
    MeProfileUserSerializer,
    RegisterSerializer,
    UserSerializer,
)
from .permissions import IsAdminRole


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]


class ProfileView(generics.RetrieveAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


@extend_schema(
    summary="Профиль текущего сотрудника",
    responses=MeProfileResponseSerializer,
)
class MeProfileView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = MeProfileResponseSerializer

    def get(self, request, *args, **kwargs):
        certificates = (
            TrainingEnrollment.objects.filter(employee=request.user, is_attended=True)
            .filter(Q(certificate_number__gt="") | Q(certificate_file__gt=""))
            .select_related("training_session__training")
            .order_by("-training_session__end_date", "-created_at")
        )

        data = {
            "user": MeProfileUserSerializer(request.user).data,
            "certificates": MeProfileCertificateSerializer(certificates, many=True).data,
        }
        return Response(data)


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by("username")
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, IsAdminRole]
