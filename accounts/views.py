from django.db.models import Q
from drf_spectacular.utils import extend_schema
from rest_framework import generics, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated

from enrollments.models import TrainingEnrollment
from .models import User
from .serializers import (
    MeProfileCertificateSerializer,
    MeProfileResponseSerializer,
    MeProfileUserSerializer,
    RegisterSerializer,
    UserNamePatchSerializer,
    UserSerializer,
)
from .permissions import IsAdminRole


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]


class ProfileView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "patch", "head", "options"]

    def get_serializer_class(self):
        if self.request.method.lower() == "patch":
            return UserNamePatchSerializer
        return UserSerializer

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

    def get_permissions(self):
        if self.action == "list":
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAuthenticated, IsAdminRole]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        queryset = User.objects.all().order_by("username")
        if self.action == "list":
            return queryset.filter(role=User.Role.EMPLOYEE).order_by("last_name", "first_name", "email")
        return queryset

    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated], url_path="employees")
    def employees(self, request, *args, **kwargs):
        if request.user.role not in [User.Role.ADMIN, User.Role.MANAGER]:
            return Response(
                {"detail": "Только администраторы и менеджеры могут просматривать список сотрудников."},
                status=status.HTTP_403_FORBIDDEN,
            )

        employees_qs = User.objects.filter(role=User.Role.EMPLOYEE).order_by("last_name", "first_name", "email")
        serializer = self.get_serializer(employees_qs, many=True)
        return Response(serializer.data)
