FROM python:3.9-slim

RUN pip install requests schedule

COPY app.py /app/app.py
CMD ["python", "/app/app.py"]