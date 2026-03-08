from django.contrib import admin
from .models import TrainingRequest, TrainingRequestEmployee


# Позволяет добавлять сотрудников прямо в окне создания заявки
class TrainingRequestEmployeeInline(admin.TabularInline):
    model = TrainingRequestEmployee
    extra = 1
    verbose_name = "Сотрудник в заявке"
    verbose_name_plural = "Сотрудники в заявке"


@admin.register(TrainingRequest)
class TrainingRequestAdmin(admin.ModelAdmin):
    list_display = ("id", "manager", "training_session", "status", "created_at")
    list_filter = ("status", "training_session", "created_at")
    search_fields = ("manager__username", "training_session__training__title")
    inlines = [TrainingRequestEmployeeInline]

    # Сценарий В из ТЗ: Ограничение видимости для руководителей
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Если пользователь не суперадмин и состоит в группе руководителей
        if not request.user.is_superuser and request.user.groups.filter(name='Department_Head').exists():
            return qs.filter(manager=request.user)
        return qs

    # Автоматически подставляем текущего пользователя в поле "Менеджер" при создании
    def save_model(self, request, obj, form, change):
        if not obj.manager_id:
            obj.manager = request.user
        super().save_model(request, obj, form, change)

    # Делаем поле менеджера только для чтения для руководителей, чтобы они не могли подать заявку от чужого имени
    def get_readonly_fields(self, request, obj=None):
        if not request.user.is_superuser:
            return ("manager",)
        return ()