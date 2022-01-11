FROM python:3.9.9-slim

ENV BOT_TOKEN=5081831798:AAGtVI6smfrDBBcno__-oHGmbbfntrKhnXQ

ENV HOST_API=http://172.17.0.2:8000/api/

ENV APIKEY=Kqild3C9.uoNiKgOGs4Zf2iDEmkyMUH2pFHIQ2TUs

WORKDIR /app

COPY requirements.txt ./

RUN python -m pip install --upgrade pip

RUN pip install -r requirements.txt

COPY . .

CMD ["python", "FinanceProjectBot.py"]

