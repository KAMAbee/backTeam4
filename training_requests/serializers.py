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
    contract = serializers.PrimaryKeyRelatedField(
        queryset=Contract.objects.all(),
        write_only=True,
        required=False
    )

    class Meta:
        model = TrainingRequest
        fields = [
            "id", "manager", "training_session", "training_title", "status",
            "comment", "created_at", "employees", "employee_ids", "contract"
        ]
        read_only_fields = ["id", "manager", "status", "created_at", "employees"]

    def validate_employee_ids(self, value):
        if not value:
            raise serializers.ValidationError("Укажите хотя бы одного сотрудника.")
        if len(value) != len(set(value)):
            raise serializers.ValidationError("Список сотрудников содержит дубликаты.")
        
        # Проверка ролей: в заявку можно добавлять только рядовых сотрудников (EMPLOYEE)
        for employee in value:
            if employee.role != User.Role.EMPLOYEE:
                raise serializers.ValidationError(
                    f"Пользователь {employee.username} имеет роль {employee.role}. "
                    "В заявку можно добавлять только рядовых сотрудников (EMPLOYEE)."
                )
        return value

    def validate(self, attrs):
        session = attrs.get("training_session")
        employee_ids = attrs.get("employee_ids")
        contract = attrs.get("contract")
        from enrollments.models import TrainingEnrollment

        if session and contract:
            training_supplier = session.training.supplier
            if training_supplier and contract.supplier_id != training_supplier.id:
                raise serializers.ValidationError("Selected contract does not belong to training supplier")
        
        if session and employee_ids:
            # 1. Проверка вместимости
            if len(employee_ids) > session.capacity:
                raise serializers.ValidationError(
                    f"Количество сотрудников ({len(employee_ids)}) превышает общую вместимость сессии ({session.capacity})."
                )
            
            # 2. Проверка, не зачислены ли они уже
            already_enrolled = TrainingEnrollment.objects.filter(
                training_session=session,
                employee__in=employee_ids
            ).values_list('employee__username', flat=True)
            
            if already_enrolled:
                names = ", ".join(already_enrolled)
                raise serializers.ValidationError(
                    f"Следующие сотрудники уже зачислены на эту сессию: {names}"
                )

            # 3. Проверка, нет ли уже активных (PENDING/APPROVED) заявок на этих сотрудников для этой сессии
            existing_requests = TrainingRequestEmployee.objects.filter(
                training_request__training_session=session,
                training_request__status__in=[TrainingRequest.Status.PENDING, TrainingRequest.Status.APPROVED],
                employee__in=employee_ids
            ).values_list('employee__username', flat=True).distinct()

            if existing_requests:
                names = ", ".join(existing_requests)
                raise serializers.ValidationError(
                    f"На следующих сотрудников уже поданы активные заявки для этой сессии: {names}"
                )
        return attrs

    def create(self, validated_data):
        employee_ids = validated_data.pop("employee_ids")
        validated_data.pop("contract", None)
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
        training_request = self.context.get("training_request")
        contract = attrs.get("contract")
        if training_request and contract:
            training_supplier = training_request.training_session.training.supplier
            if training_supplier and contract.supplier_id != training_supplier.id:
                raise serializers.ValidationError("Selected contract does not belong to training supplier")
        return attrs
