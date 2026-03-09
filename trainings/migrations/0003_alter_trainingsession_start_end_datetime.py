from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("trainings", "0002_alter_training_options_alter_trainingsession_options_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="trainingsession",
            name="start_date",
            field=models.DateTimeField(verbose_name="Дата и время начала"),
        ),
        migrations.AlterField(
            model_name="trainingsession",
            name="end_date",
            field=models.DateTimeField(verbose_name="Дата и время окончания"),
        ),
    ]

