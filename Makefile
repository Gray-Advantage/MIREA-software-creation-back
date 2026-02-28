COMPOSE = docker compose -f docker/docker-compose.yml

.PHONY: run stop restart build status migrate shell-django shell-api createsuperuser clean lint ruff check-api

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

lint:
	ruff check . --fix
	ruff format .

