FROM python:3.9-slim AS build

WORKDIR /app

# Setup venv
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

RUN pip install --no-cache-dir requests schedule

FROM gcr.io/distroless/python3-debian12

WORKDIR /app

# Copy venv
COPY --from=build /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY app.py .
CMD ["/app/app.py"]