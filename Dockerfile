FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends     ffmpeg libass9 fonts-noto-core fonts-noto-cjk     && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY static ./static
RUN mkdir -p /app/data

ENV PYTHONUNBUFFERED=1
EXPOSE 10000

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-10000}"]
