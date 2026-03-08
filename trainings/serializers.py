from rest_framework import serializers
from .models import Training, TrainingSession

class TrainingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Training
        fields = '__all__'

class TrainingSessionSerializer(serializers.ModelSerializer):
    training_detail = TrainingSerializer(source='training', read_only=True)
    class Meta:
        model = TrainingSession
        fields = '__all__'