# syntax=docker/dockerfile:1

FROM python:3.9.10

COPY requirements.txt app/requirements.txt
RUN pip install -r app/requirements.txt

COPY firebasecred.json firebasecred.json
COPY .prodenv .env
COPY /src /app

CMD ["python", "app/bot.py"]