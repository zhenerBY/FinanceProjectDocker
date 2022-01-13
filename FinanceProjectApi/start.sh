#!/usr/bin/env bash

python manage.py migrate
python manage.py shell -c "from rest_framework_api_key.models import APIKey; api_key, key = APIKey.objects.create_key(name='docker'); f = open('key', 'w'); f.write(key); f.close()"
#python manage.py runserver 0.0.0.0:8000
gunicorn -b 0.0.0.0:8000 config.wsgi --log-file -