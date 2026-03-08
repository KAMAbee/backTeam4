from rest_framework import serializers
from .models import TrainingEnrollment

class TrainingEnrollmentSerializer(serializers.ModelSerializer):
    training_title = serializers.CharField(source='training_session.training.title', read_only=True)
    start_date = serializers.DateField(source='training_session.start_date', read_only=True)
    end_date = serializers.DateField(source='training_session.end_date', read_only=True)

    class Meta:
        model = TrainingEnrollment
        fields = ['id', 'training_title', 'start_date', 'end_date', 'is_attended', 'certificate_file', 'certificate_number']
        read_only_fields = ['id', 'is_attended', 'certificate_file', 'certificate_number']

class AdminEnrollmentUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrainingEnrollment
        fields = ['is_attended', 'certificate_file', 'certificate_number']