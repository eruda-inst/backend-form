FROM python:3.11

WORKDIR /app
COPY start.sh /start.sh
RUN chmod +x /start.sh

RUN apt-get update && apt-get install -y netcat-openbsd

COPY wait-for.sh /wait-for.sh
RUN chmod +x /wait-for.sh

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["/wait-for.sh", "db", "5432", "--", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

