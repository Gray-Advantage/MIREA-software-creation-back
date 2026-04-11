COMPOSE = docker compose -f docker/docker-compose.yml
PYTHON  = python3

.PHONY: run stop restart build status migrate shell-django shell-api createsuperuser clean lint ruff mypy check-api test test-cov

run:
	$(COMPOSE) up -d --build

stop:
	$(COMPOSE) down

restart: stop run

build:
	$(COMPOSE) build

status:
	$(COMPOSE) ps

migration:
	$(COMPOSE) exec api sh -c "cd /code/api && alembic revision --autogenerate -m '$(msg)'"

migrate:
	$(COMPOSE) exec api sh -c "cd /code/api && alembic upgrade head"

shell-django:
	$(COMPOSE) exec django python manage.py shell

shell-api:
	$(COMPOSE) exec api sh

createsuperuser:
	$(COMPOSE) exec django python manage.py createsuperuser

clean:
	$(COMPOSE) down --rmi local

ruff:
	ruff check . --fix
	ruff format .

mypy:
	$(PYTHON) -m mypy api

lint: ruff mypy

test:
	$(PYTHON) -m pytest -vvvv --ff $(ARGS)

test-cov:
	$(PYTHON) -m pytest -vvvv --ff --cov=api --cov-report=term-missing --cov-report=html $(ARGS)

