FROM python:3.9-slim

WORKDIR /app

RUN pip install --no-cache-dir requests schedule

ENV PYTHONUNBUFFERED=1

COPY app.py .
CMD ["python", "/app/app.py"]