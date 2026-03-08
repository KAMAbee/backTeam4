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
        from django.db.models import Sum, Q
        from decimal import Decimal
        
        start_date = attrs.get("start_date")
        end_date = attrs.get("end_date")
        total_amount = attrs.get("total_amount")
        supplier = attrs.get("supplier")

        # 1. Проверка дат (начало < конец)
        if start_date and end_date and end_date < start_date:
            raise serializers.ValidationError(
                {"end_date": "Дата окончания не может быть раньше даты начала."}
            )

        # 2. Проверка бюджета при обновлении
        if self.instance and total_amount is not None:
            allocated_total = self.instance.contractallocation_set.aggregate(
                total=Sum("allocated_amount")
            )["total"] or Decimal(0)
            
            if total_amount < allocated_total:
                raise serializers.ValidationError(
                    {"total_amount": f"Сумма контракта не может быть меньше уже выделенных средств ({allocated_total})."}
                )

        # 3. Проверка на пересечение дат для одного поставщика
        # При создании берем supplier из attrs, при обновлении - из инстанса
        target_supplier = supplier or (self.instance.supplier if self.instance else None)
        target_start = start_date or (self.instance.start_date if self.instance else None)
        target_end = end_date or (self.instance.end_date if self.instance else None)

        if target_supplier and target_start and target_end:
            overlap_query = Contract.objects.filter(
                supplier=target_supplier,
                start_date__lte=target_end,
                end_date__gte=target_start
            )
            if self.instance:
                overlap_query = overlap_query.exclude(pk=self.instance.pk)
            
            if overlap_query.exists():
                raise serializers.ValidationError(
                    "У этого поставщика уже есть контракт на указанный период."
                )

        return attrs