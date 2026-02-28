FROM python:3.12-alpine

WORKDIR /code

COPY requirements/base.txt requirements/base.txt
COPY requirements/django.txt requirements/django.txt
RUN apk add --no-cache --virtual .build-deps gcc musl-dev libffi-dev postgresql-dev \
    && pip install --no-cache-dir -r requirements/django.txt \
    && apk del .build-deps

COPY admin-panel/ admin-panel/

WORKDIR /code/admin-panel

CMD ["sh", "-c", "python manage.py migrate --noinput && python manage.py collectstatic --noinput && python manage.py createsuperuser --noinput 2>/dev/null; gunicorn app.wsgi:application --bind 0.0.0.0:8000"]
