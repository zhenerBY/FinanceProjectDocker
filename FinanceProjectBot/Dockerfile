FROM python:3.9.9-slim

ENV BOT_TOKEN=5081831798:AAGtVI6smfrDBBcno__-oHGmbbfntrKhnXQ

ENV HOST_API=http://api:8000/api/

#ENV APIKEY=FI7ufOCX.m9f0VTk7d4I5lIQqu5iFo3heyqJDCxcX

WORKDIR /app

COPY requirements.txt ./

RUN python -m pip install --upgrade pip

RUN pip install -r requirements.txt

COPY . .

#CMD ["python", "FinanceProjectBot.py"]
