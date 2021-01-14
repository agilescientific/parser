FROM tiangolo/uvicorn-gunicorn-fastapi:python3.8

LABEL maintainer="Agile Scientific"

COPY requirements.txt /app/requirements.txt

RUN pip install -r /app/requirements.txt

COPY ./ /app