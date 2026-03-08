from rest_framework import serializers
from .models import Contract, Supplier


class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = "__all__"


class ContractSerializer(serializers.ModelSerializer):
    # Достаем имя поставщика из связанной модели Supplier (только для чтения)
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)

    # Поле для выбора поставщика при создании/редактировании (ID)
    supplier = serializers.PrimaryKeyRelatedField(queryset=Supplier.objects.all())

    class Meta:
        model = Contract
        fields = [
            "id",
            "supplier",  # ID поставщика (для записи)
            "supplier_name",  # Имя поставщика (для отображения фронтенду)
            "contract_number",
            "start_date",
            "end_date",
            "total_amount",
            "created_at",
        ]
        read_only_fields = ["id", "created_at", "supplier_name"]

    def validate(self, attrs):
        start_date = attrs.get("start_date")
        end_date = attrs.get("end_date")

        # Проверка дат
        if start_date and end_date and end_date < start_date:
            raise serializers.ValidationError(
                {"end_date": "Дата окончания не может быть раньше даты начала."}
            )

        return attrs