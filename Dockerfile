# Cloud Run injects a $PORT env var and expects the container to listen on
# it — that's the one Cloud-Run-specific detail here, everything else is a
# normal FastAPI/uvicorn container.

FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/

ENV PORT=8080
EXPOSE 8080

CMD exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT}
