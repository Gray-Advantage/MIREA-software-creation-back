FROM python:3.12-slim

WORKDIR /code

COPY requirements/base.txt requirements/base.txt
COPY requirements/api.txt requirements/api.txt
RUN pip install --no-cache-dir -r requirements/api.txt

COPY api/ api/
COPY docker/bonus.jpg docker/fine.jpg docker/

CMD ["sh", "-c", "cd /code/api && alembic upgrade head && exec uvicorn api.main:app --host 0.0.0.0 --port 8001 --app-dir /code"]
