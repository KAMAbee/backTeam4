import json

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiExample, OpenApiParameter, extend_schema, inline_serializer
from rest_framework import mixins, permissions, serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response

from .models import TrainingEnrollment
from .serializers import (
    AdminEnrollmentUpdateSerializer,
    EnrollmentParticipantsBulkPatchItemSerializer,
    SessionParticipantSerializer,
    TrainingEnrollmentSerializer,
)
from accounts.permissions import IsAdminRole


class MyEnrollmentsViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TrainingEnrollmentSerializer

    def get_queryset(self):
        return TrainingEnrollment.objects.filter(employee=self.request.user).select_related("training_session__training")


class AdminEnrollmentViewSet(mixins.UpdateModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = TrainingEnrollment.objects.all()
    serializer_class = AdminEnrollmentUpdateSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminRole]
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def _session_queryset(self, session_id):
        return TrainingEnrollment.objects.filter(training_session_id=session_id).select_related(
            "employee", "training_session__training"
        )

    @extend_schema(
        summary="Участники сессии обучения",
        description="Список всех зачислений в указанной training session.",
        parameters=[
            OpenApiParameter(
                name="session_id",
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.PATH,
                required=True,
            )
        ],
        responses=SessionParticipantSerializer(many=True),
    )
    @action(
        detail=False,
        methods=["get", "patch"],
        url_path=r"session/(?P<session_id>[^/.]+)/participants",
        url_name="session-participants",
    )
    def session_participants(self, request, session_id=None):
        session_enrollments = self._session_queryset(session_id).order_by(
            "employee__last_name", "employee__first_name", "employee__email"
        )

        if request.method.lower() == "get":
            serializer = SessionParticipantSerializer(session_enrollments, many=True)
            return Response(serializer.data)

        return self._bulk_patch_session_participants(request, session_id, session_enrollments)

    @extend_schema(
        request=inline_serializer(
            name="EnrollmentParticipantsBulkPatchRequest",
            fields={
                "items": serializers.CharField(
                    help_text="JSON array of objects: enrollment_id, is_attended, certificate_number"
                )
            },
        ),
        examples=[
            OpenApiExample(
                "BulkPatchBody",
                value={
                    "items": (
                        '[{"enrollment_id":"0a5d8f7e-2df8-4f0a-8ad4-4aee36d51918","is_attended":true,'
                        '"certificate_number":"ABC-1"}]'
                    )
                },
                request_only=True,
            )
        ],
        responses=SessionParticipantSerializer(many=True),
    )
    def _bulk_patch_session_participants(self, request, session_id, session_enrollments):
        if isinstance(request.data, list):
            items_raw = request.data
        else:
            items_raw = request.data.get("items", request.data)
        if isinstance(items_raw, str):
            try:
                items = json.loads(items_raw)
            except json.JSONDecodeError:
                return Response({"detail": "Invalid JSON in `items` field."}, status=status.HTTP_400_BAD_REQUEST)
        else:
            items = items_raw

        if not isinstance(items, list):
            return Response({"detail": "`items` must be a JSON array."}, status=status.HTTP_400_BAD_REQUEST)

        for item in items:
            enrollment_id = item.get("enrollment_id")
            if enrollment_id:
                file_key = f"files.{enrollment_id}"
                if file_key in request.FILES:
                    item["certificate_file"] = request.FILES[file_key]

        serializer = EnrollmentParticipantsBulkPatchItemSerializer(
            data=items, many=True, context={"session_id": session_id}
        )
        serializer.is_valid(raise_exception=True)

        enrollments_by_id = session_enrollments.in_bulk(field_name="id")

        for item in serializer.validated_data:
            enrollment = enrollments_by_id[item["enrollment_id"]]
            update_fields = []
            for field in ("is_attended", "certificate_number", "certificate_file"):
                if field in item:
                    setattr(enrollment, field, item[field])
                    update_fields.append(field)
            if update_fields:
                enrollment.save(update_fields=update_fields)

        response_serializer = SessionParticipantSerializer(
            self._session_queryset(session_id).order_by("employee__last_name", "employee__first_name", "employee__email"),
            many=True,
        )
        return Response(response_serializer.data, status=status.HTTP_200_OK)
