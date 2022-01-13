#!/usr/bin/env bash

python manage.py migrate
python manage.py shell -c "from main.models import AdvUser; AdvUser.objects.create_superuser('admin', 'admin@example.com', 'admin')"
python manage.py shell -c "from rest_framework_api_key.models import APIKey; api_key, key = APIKey.objects.create_key(name='docker'); f = open('key', 'w'); f.write(key); f.close()"
python manage.py runserver 0.0.0.0:8000