from rest_framework import serializers

from .models import TrainingEnrollment


def _build_fio(user):
    return " ".join(filter(None, [user.last_name, user.first_name, user.patronymic])).strip()

class TrainingEnrollmentSerializer(serializers.ModelSerializer):
    training_title = serializers.CharField(source='training_session.training.title', read_only=True)
    start_date = serializers.DateTimeField(source='training_session.start_date', read_only=True)
    end_date = serializers.DateTimeField(source='training_session.end_date', read_only=True)
    location = serializers.CharField(source="training_session.location", read_only=True)
    city = serializers.CharField(source="training_session.city", read_only=True)

    class Meta:
        model = TrainingEnrollment
        fields = [
            'id',
            'training_title',
            'start_date',
            'end_date',
            'location',
            'city',
            'is_attended',
            'certificate_file',
            'certificate_number',
        ]
        read_only_fields = ['id', 'is_attended', 'certificate_file', 'certificate_number']

class AdminEnrollmentUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrainingEnrollment
        fields = ["is_attended", "certificate_file", "certificate_number"]


class SessionParticipantEmployeeSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    fio = serializers.SerializerMethodField()
    email = serializers.EmailField(read_only=True)

    def get_fio(self, obj) -> str:
        return _build_fio(obj)


class SessionParticipantSerializer(serializers.ModelSerializer):
    enrollment_id = serializers.UUIDField(source="id", read_only=True)
    employee = SessionParticipantEmployeeSerializer(read_only=True)
    training_title = serializers.CharField(source="training_session.training.title", read_only=True)
    start_date = serializers.DateTimeField(source="training_session.start_date", read_only=True)
    end_date = serializers.DateTimeField(source="training_session.end_date", read_only=True)

    class Meta:
        model = TrainingEnrollment
        fields = [
            "enrollment_id",
            "employee",
            "training_title",
            "start_date",
            "end_date",
            "is_attended",
            "certificate_number",
            "certificate_file",
        ]


class EnrollmentParticipantsBulkPatchListSerializer(serializers.ListSerializer):
    def validate(self, attrs):
        enrollment_ids = [item["enrollment_id"] for item in attrs]
        duplicates = {enrollment_id for enrollment_id in enrollment_ids if enrollment_ids.count(enrollment_id) > 1}
        if duplicates:
            raise serializers.ValidationError(
                {"enrollment_id": f"Duplicate enrollment_id values: {', '.join(map(str, duplicates))}"}
            )

        session_id = self.context.get("session_id")
        existing_ids = set(
            TrainingEnrollment.objects.filter(training_session_id=session_id, id__in=enrollment_ids).values_list(
                "id", flat=True
            )
        )
        missing = [str(enrollment_id) for enrollment_id in enrollment_ids if enrollment_id not in existing_ids]
        if missing:
            raise serializers.ValidationError(
                {"enrollment_id": f"Enrollment(s) do not belong to this session: {', '.join(missing)}"}
            )
        return attrs


class EnrollmentParticipantsBulkPatchItemSerializer(serializers.Serializer):
    enrollment_id = serializers.UUIDField()
    is_attended = serializers.BooleanField(required=False)
    certificate_number = serializers.CharField(required=False, allow_blank=True, max_length=100)
    certificate_file = serializers.FileField(required=False, allow_null=True)

    class Meta:
        list_serializer_class = EnrollmentParticipantsBulkPatchListSerializer

    def validate(self, attrs):
        if len(attrs) == 1 and "enrollment_id" in attrs:
            raise serializers.ValidationError("Provide at least one updatable field.")
        return attrs
