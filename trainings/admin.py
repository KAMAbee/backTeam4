from django.contrib import admin
from .models import Training, TrainingSession

@admin.register(Training)
class TrainingAdmin(admin.ModelAdmin):
    # Показываем название, тип, тренера и цену самого курса
    list_display = ("title", "type", "trainer_name", "price", "pricing_type")
    list_filter = ("type", "pricing_type")
    search_fields = ("title", "trainer_name")

@admin.register(TrainingSession)
class TrainingSessionAdmin(admin.ModelAdmin):
    # Показываем курс, даты, город и вместимость сессии
    list_display = ("training", "start_date", "end_date", "city", "capacity")
    list_filter = ("start_date", "city", "training")
    search_fields = ("city", "training__title")