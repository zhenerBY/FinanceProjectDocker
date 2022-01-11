FROM python:3.9.9-slim

ENV BOT_TOKEN=5081831798:AAGtVI6smfrDBBcno__-oHGmbbfntrKhnXQ

ENV HOST_API=bot/api/

ENV APIKEY=ou8B7Cv8imHtpTXxkp6SINZf74oXBhUo

WORKDIR /app

COPY requirements.txt ./

RUN python -m pip install --upgrade pip

RUN pip install -r requirements.txt

COPY . .

#EXPOSE 7000

CMD ["python", "FinanceProjectBot.py"]

