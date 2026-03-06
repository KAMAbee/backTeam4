from rest_framework import serializers
from .models import TrainingRequest, TrainingRequestEmployee
from accounts.models import User
from trainings.models import TrainingSession, Training
from suppliers.models import Contract


class TrainingRequestEmployeeSerializer(serializers.ModelSerializer):
    employee_name = serializers.SerializerMethodField()

    class Meta:
        model = TrainingRequestEmployee
        fields = ["id", "employee", "employee_name"]

    def get_employee_name(self, obj):
        return f"{obj.employee.last_name} {obj.employee.first_name}"


class TrainingRequestSerializer(serializers.ModelSerializer):
    employees = TrainingRequestEmployeeSerializer(many=True, read_only=True)
    employee_ids = serializers.ListField(
        child=serializers.PrimaryKeyRelatedField(queryset=User.objects.all()),
        write_only=True,
        required=True
    )
    training_title = serializers.CharField(source="training_session.training.title", read_only=True)

    class Meta:
        model = TrainingRequest
        fields = [
            "id", "manager", "training_session", "training_title", "status",
            "comment", "created_at", "employees", "employee_ids"
        ]
        read_only_fields = ["id", "manager", "status", "created_at", "employees"]

    def validate_employee_ids(self, value):
        if not value:
            raise serializers.ValidationError("Укажите хотя бы одного сотрудника.")
        return value

    def create(self, validated_data):
        employee_ids = validated_data.pop("employee_ids")
        request = self.context.get("request")
        user = request.user if request else None
        
        training_request = TrainingRequest.objects.create(
            manager=user,
            status=TrainingRequest.Status.PENDING,
            **validated_data
        )
        
        for employee in employee_ids:
            TrainingRequestEmployee.objects.create(
                training_request=training_request,
                employee=employee
            )
            
        return training_request


class ApproveRequestSerializer(serializers.Serializer):
    contract = serializers.PrimaryKeyRelatedField(queryset=Contract.objects.all())

    def validate(self, attrs):
        # business logic validation in the view to access the training request instance
        return attrs
