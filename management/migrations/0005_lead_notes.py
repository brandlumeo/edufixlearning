from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("management", "0004_supportticket_lead"),
    ]

    operations = [
        migrations.AddField(
            model_name="lead",
            name="notes",
            field=models.TextField(blank=True, help_text="Internal notes from staff"),
        ),
    ]
