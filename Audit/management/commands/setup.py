from pathlib import Path

import environ
from django.core.management.base import BaseCommand
from django.conf import settings
from django.contrib.auth.models import Group  # Import the Group model
from django.core.files import File
from Audit.models import OWL_Upload, OWL_Upload_Configs
import os
import django
from django.contrib.auth.models import User


env = environ.Env()
environ.Env.read_env()

class Command(BaseCommand):
    help = 'Sets up the database, runs migrations, populates the Question_type table, and creates an Analyst user group.'

    def handle(self, *args, **kwargs):
        # Debugging: Check environment variable values
        db_engine = env('DB_ENGINE', default='sqlite3').strip()
        raw_db_name = env('DB_NAME', default='').strip()
        db_name = raw_db_name if raw_db_name not in ("", "placeholder_db_name") else "db"
        
        # Print to see if the environment values are correct
        
        if db_engine == 'sqlite3':
            self.stdout.write(self.style.SUCCESS(f"Using SQLite database '{db_name}'."))

        else:
            self.stdout.write(self.style.ERROR(f"Unsupported DB_ENGINE: {db_engine}"))
            return

        # Now run migrations using Django's connection (after the DB is created)
        if settings.DATABASES['default']['ENGINE'] == 'django.db.backends.sqlite3':
            normalized_name = settings.DATABASES['default']['NAME']
            sqlite_path = Path(normalized_name) if isinstance(normalized_name, str) else normalized_name
            if sqlite_path.suffix.lower() != '.sqlite3':
                sqlite_path = sqlite_path.with_suffix('.sqlite3')
            settings.DATABASES['default']['NAME'] = sqlite_path
        else:
            settings.DATABASES['default']['NAME'] = db_name
        from django.core.management import call_command
        call_command('migrate')

        # Save OWL file
        if OWL_Upload.objects.exists():
            self.stdout.write("OWL files already exist in the database. Skipping upload.")
        else:
            for owl_path in ["Example/NewStarT.owl", "Example/template.owl"]:
                if os.path.exists(owl_path):
                    with open(owl_path, "rb") as f:
                        obj = OWL_Upload.objects.create()
                        obj.file.save(owl_path, File(f), save=True)

                    self.stdout.write("OWL file saved")

        # Save config file content
        if OWL_Upload_Configs.objects.exists():
            self.stdout.write("Config already exists in the database. Skipping upload.")
        else:
            for yml_path in [("Example/NewStarT.yml", "NewStarT"), ("Example/template.yml", "template")]:
                if os.path.exists(yml_path[0]):
                    with open(yml_path[0], "r") as f:
                        content = f.read()

                    OWL_Upload_Configs.objects.create(configs=content, name=yml_path[1])
                    self.stdout.write("Config saved")
        
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "root.settings")
        django.setup()

        if not User.objects.exists():
            username = os.environ.get("DJANGO_SUPERUSER_USERNAME", "admin")
            email = os.environ.get("DJANGO_SUPERUSER_EMAIL", "admin@example.com")
            password = os.environ.get("DJANGO_SUPERUSER_PASSWORD", "1234")

            if not User.objects.filter(username=username).exists():
                User.objects.create_superuser(username=username, email=email, password=password)
                print(f"Superuser {username} created.")
            else:
                print(f"Superuser {username} already exists.")
