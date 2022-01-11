FROM python:3.9.9-slim

ENV SECRET_KEY=django-insecure-xokz#o4hk#ix19yi77rr#&kqj*mnk78z@n61$f)*2omh(6lo&_

WORKDIR /app

COPY requirements.txt ./

RUN python -m pip install --upgrade pip

RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

