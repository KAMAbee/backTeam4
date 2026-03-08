from rest_framework import serializers
from .models import Training, TrainingSession

class TrainingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Training
        fields = '__all__'

    def validate_price(self, value):
        if value < 0:
            raise serializers.ValidationError("Цена не может быть отрицательной.")
        return value

class TrainingSessionSerializer(serializers.ModelSerializer):
    training_detail = TrainingSerializer(source='training', read_only=True)
    class Meta:
        model = TrainingSession
        fields = '__all__'

    def validate(self, attrs):
        start_date = attrs.get('start_date')
        end_date = attrs.get('end_date')

        if start_date and end_date and end_date < start_date:
            raise serializers.ValidationError({"end_date": "Дата окончания не может быть раньше даты начала."})
        return attrs