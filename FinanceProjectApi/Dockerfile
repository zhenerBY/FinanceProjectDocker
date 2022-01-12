FROM python:3.9.9-slim

ENV SECRET_KEY=django-insecure-xokz#o4hk#ix19yi77rr#&kqj*mnk78z@n61$f)*2omh(6lo&_

WORKDIR /app

COPY requirements.txt ./

RUN python -m pip install --upgrade pip

RUN pip install -r requirements.txt

COPY . .

#RUN python manage.py shell -c "from rest_framework_api_key.models import APIKey; api_key, key = APIKey.objects.create_key(name='docker'); with open('apikey', 'w') as f: f.write(key)"

EXPOSE 8000

CMD ["gunicorn", "-b 0.0.0.0:8000", "config.wsgi", "--log-file -"]
#CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
