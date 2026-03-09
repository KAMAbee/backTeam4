from rest_framework import serializers

from enrollments.models import TrainingEnrollment

from .models import User


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "password",
            "first_name",
            "last_name",
            "patronymic",
            "role",
            "department",
        )
        read_only_fields = ("id",)

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(source="department.name", read_only=True)

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "patronymic",
            "role",
            "department",
            "department_name",
            "created_at",
        )
        read_only_fields = ("id", "created_at", "department_name")


class UserNamePatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("first_name", "last_name")
        extra_kwargs = {
            "first_name": {"required": False, "allow_blank": False},
            "last_name": {"required": False, "allow_blank": False},
        }

    def validate(self, attrs):
        if not attrs:
            raise serializers.ValidationError("Передайте first_name и/или last_name.")
        return attrs


class MeProfileUserSerializer(serializers.ModelSerializer):
    fio = serializers.SerializerMethodField()
    department = serializers.CharField(source="department.name", read_only=True)
    organization = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ("id", "fio", "email", "role", "department", "organization")

    def get_fio(self, obj) -> str:
        return " ".join(filter(None, [obj.last_name, obj.first_name, obj.patronymic])).strip()

    def get_organization(self, obj) -> str | None:
        if obj.department and obj.department.organization:
            return obj.department.organization.name
        return None


class MeProfileCertificateSerializer(serializers.ModelSerializer):
    enrollment_id = serializers.UUIDField(source="id", read_only=True)
    training_title = serializers.CharField(source="training_session.training.title", read_only=True)
    start_date = serializers.DateTimeField(source="training_session.start_date", read_only=True)
    end_date = serializers.DateTimeField(source="training_session.end_date", read_only=True)
    location = serializers.CharField(source="training_session.location", read_only=True)
    city = serializers.CharField(source="training_session.city", read_only=True)

    class Meta:
        model = TrainingEnrollment
        fields = (
            "enrollment_id",
            "training_title",
            "start_date",
            "end_date",
            "location",
            "city",
            "is_attended",
            "certificate_number",
            "certificate_file",
        )


class MeProfileResponseSerializer(serializers.Serializer):
    user = MeProfileUserSerializer()
    certificates = MeProfileCertificateSerializer(many=True)
