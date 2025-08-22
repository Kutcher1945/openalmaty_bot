FROM python:3.11

# Установим зависимости для psycopg2
RUN apt-get update && apt-get install -y \
    gcc libpq-dev python3-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Скопируем зависимости
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Скопируем исходники
COPY . .

CMD ["python", "bot.py"]
