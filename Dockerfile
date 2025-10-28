FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y netcat-openbsd && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chmod +x /app/start.sh /app/wait-for.sh

ARG APP_VERSION=dev
ENV BACKEND_VERSION=${APP_VERSION}
LABEL org.opencontainers.image.version=${APP_VERSION}

CMD ["/app/wait-for.sh","db","5432","--","/app/start.sh"]
