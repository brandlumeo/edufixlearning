from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("management", "0006_batch_scheduling_details"),
    ]

    operations = [
        migrations.AddField(
            model_name="batch",
            name="batch_code",
            field=models.CharField(blank=True, help_text="Short ID/code e.g. PR-01", max_length=20),
        ),
        migrations.AddField(
            model_name="batch",
            name="status",
            field=models.CharField(
                choices=[("upcoming", "Upcoming"), ("active", "Active"), ("completed", "Completed")],
                default="upcoming",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="batch",
            name="mode",
            field=models.CharField(
                choices=[("online", "Online"), ("offline", "Offline"), ("hybrid", "Hybrid")],
                default="offline",
                max_length=10,
            ),
        ),
        migrations.AddField(
            model_name="batch",
            name="total_classes",
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name="batch",
            name="completed_classes",
            field=models.IntegerField(default=0),
        ),
    ]
