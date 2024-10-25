FROM gcr.io/distroless/python3-debian12

WORKDIR /app
ENV PYTHONUNBUFFERED=1

RUN pip install --no-cache-dir requests schedule

COPY app.py .
CMD ["/app/app.py"]