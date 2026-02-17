from pathlib import Path

import environ
from django.core.management.base import BaseCommand
from django.conf import settings
import MySQLdb
from django.contrib.auth.models import Group  # Import the Group model

env = environ.Env()
environ.Env.read_env()

class Command(BaseCommand):
    help = 'Sets up the database, runs migrations, populates the Question_type table, and creates an Analyst user group.'

    def handle(self, *args, **kwargs):
        # Debugging: Check environment variable values
        db_engine = env('DB_ENGINE', default='sqlite3').strip()
        raw_db_name = env('DB_NAME', default='').strip()
        db_name = raw_db_name if raw_db_name not in ("", "placeholder_db_name") else "db"
        db_host = env('DB_HOST', default='not_set')
        db_port = env('DB_PORT', default='3306')
        db_user = env('DB_USER', default='not_set')
        db_user = env('SCORE_UPDATE_DELAY', default='300')
        db_password = env('DB_PASSWORD', default='not_set')
        
        # Print to see if the environment values are correct
        
        if db_engine == 'mysql':
            try:
                # Connect to MySQL server without specifying the database
                connection = MySQLdb.connect(
                    host=db_host,
                    user=db_user,
                    password=db_password,
                    port=int(db_port),
                )
                connection.autocommit(True)
                cursor = connection.cursor()

                cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name}")
                self.stdout.write(self.style.SUCCESS(f"Database '{db_name}' created or already exists."))
            except MySQLdb.Error as e:
                self.stdout.write(self.style.ERROR(f"Error creating database: {e}"))
                return
            finally:
                if 'cursor' in locals():
                    cursor.close()
                if 'connection' in locals():
                    connection.close()

        elif db_engine == 'sqlite3':
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
