from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0006_seed_new_program_courses'),
    ]

    operations = [
        migrations.AddField(
            model_name='certificate',
            name='is_approved',
            field=models.BooleanField(default=False, help_text='Admin must approve before student can download'),
        ),
    ]
