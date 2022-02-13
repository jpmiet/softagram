# syntax=docker/dockerfile:1
FROM tiangolo/meinheld-gunicorn-flask:python3.8
WORKDIR /app
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt
COPY . /app
RUN python3 init_db.py
