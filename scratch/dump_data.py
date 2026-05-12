import os
import sys
import django
import json
from django.core import serializers

# Add the parent directory (project root) to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'edufix_lms.settings')
django.setup()

def dump_data():
    from django.apps import apps
    
    # Get all models except the ones we want to exclude
    excluded_apps = ['auth.permission', 'contenttypes']
    models = []
    for app_config in apps.get_app_configs():
        for model in app_config.get_models():
            model_label = f"{app_config.label}.{model._meta.model_name}"
            if model_label not in excluded_apps:
                models.extend(model.objects.all())

    print(f"Serializing {len(models)} objects... please wait.")
    
    # Explicitly use utf-8 encoding to handle emojis
    with open('data_production.json', 'w', encoding='utf-8') as f:
        serializers.serialize('json', models, stream=f, indent=4)
    
    print("Successfully created 'data_production.json' with UTF-8 encoding!")

if __name__ == "__main__":
    dump_data()
