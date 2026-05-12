from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("management", "0005_lead_notes"),
    ]

    operations = [
        migrations.AddField(
            model_name="batch",
            name="end_date",
            field=models.DateField(
                blank=True,
                help_text="Last scheduled day of this batch (optional).",
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="batch",
            name="location",
            field=models.CharField(
                blank=True,
                help_text="Room, campus, lab name, or Online.",
                max_length=200,
            ),
        ),
        migrations.AddField(
            model_name="batch",
            name="online_meeting_url",
            field=models.URLField(
                blank=True,
                help_text="Zoom, Google Meet, Microsoft Teams, or other class link.",
                max_length=500,
            ),
        ),
    ]
