.PHONY: run stop restart build status migrate shell-django shell-api createsuperuser clean

# Поднять все контейнеры
run:
	docker compose up -d --build

# Остановить все контейнеры
stop:
	docker compose down

# Перезапустить все контейнеры
restart: stop run

# Собрать образы без запуска
build:
	docker compose build

# Статус контейнеров
status:
	docker compose ps

# Alembic: сгенерировать миграцию (msg="описание")
migration:
	docker compose exec api sh -c "cd /code/api && alembic revision --autogenerate -m '$(msg)'"

# Alembic: применить миграции
migrate:
	docker compose exec api sh -c "cd /code/api && alembic upgrade head"

# Django shell
shell-django:
	docker compose exec django python manage.py shell

# Bash в контейнере API
shell-api:
	docker compose exec api sh

# Создать суперпользователя Django вручную
createsuperuser:
	docker compose exec django python manage.py createsuperuser

# Удалить все контейнеры, volumes и образы
clean:
	docker compose down -v --rmi local
