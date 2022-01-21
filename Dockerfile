# syntax=docker/dockerfile:1

FROM python:3.9.10
WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN pip install -r requirements.txt
COPY /src /app
CMD ["python", "bot.py"]