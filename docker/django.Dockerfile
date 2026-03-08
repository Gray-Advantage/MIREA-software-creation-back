FROM python:3.12-slim

WORKDIR /code

RUN apt-get update \
 && apt-get install -y --no-install-recommends libpq-dev \
 && rm -rf /var/lib/apt/lists/*

COPY requirements/base.txt requirements/base.txt
COPY requirements/django.txt requirements/django.txt
RUN pip install --no-cache-dir -r requirements/django.txt

COPY admin-panel/ admin-panel/

WORKDIR /code/admin-panel

CMD ["sh", "-c", "python manage.py migrate --noinput && python manage.py collectstatic --noinput && python manage.py createsuperuser --noinput 2>/dev/null; gunicorn app.wsgi:application --bind 0.0.0.0:8000"]
