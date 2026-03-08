from django.contrib import admin
from .models import TrainingEnrollment


@admin.register(TrainingEnrollment)
class TrainingEnrollmentAdmin(admin.ModelAdmin):
    # Что видим в списке
    list_display = (
        'employee',
        'training_session',
        'is_attended',
        'certificate_number',
        'has_certificate_file',  # Добавим проверку наличия файла
        'created_at'
    )

    # Что можно менять прямо из списка (не заходя внутрь)
    list_editable = ('is_attended', 'certificate_number')

    # Фильтры справа
    list_filter = (
        'is_attended',
        'training_session__training',
        'training_session__city'
    )

    # Поиск
    search_fields = ('employee__username', 'employee__first_name', 'certificate_number')

    # Красивая иконка в списке: загружен файл или нет
    def has_certificate_file(self, obj):
        return bool(obj.certificate_file)

    has_certificate_file.boolean = True
    has_certificate_file.short_description = "Файл"