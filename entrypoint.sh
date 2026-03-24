#!/bin/sh
echo "Running migrations..."
python manage.py migrate
if python manage.py shell -c "from django.contrib.auth import get_user_model; exit(0 if get_user_model().objects.filter(username='$DJANGO_SUPERUSER_USERNAME').exists() else 1)"; then
  echo "Superuser already exists"
else
  echo "Running setup.py"
  python manage.py setup
fi
python manage.py runserver 0.0.0.0:8000