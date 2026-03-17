#!/bin/sh

DB_PATH="/app/db.sqlite3"

if [ ! -f "$DB_PATH" ]; then
  echo "Database does not exist. Calling setup."
  python manage.py setup
  python manage.py createsuperuser --noinput --username admin --password 1234
else
  echo "Database already exists. Skipping setup."
fi
python manage.py migrate

python manage.py runserver 0.0.0.0:8000