FROM python:3.11-slim

RUN echo "deb http://ftp.ru.debian.org/debian stable main" > /etc/apt/sources.list && \
    apt-get update && \
    apt-get install -y \
        build-essential \
        libpq-dev \
        curl && \
    rm -rf /var/lib/apt/lists/*


WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN python manage.py collectstatic --noinput

CMD ["gunicorn", "bronkz.wsgi:application", "--bind", "0.0.0.0:8000"]
