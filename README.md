# StaffTracker Backend

Система учёта сотрудников, рабочего времени и зарплат.

- **FastAPI** (порт 8001) — REST API для фронтенда
- **Django** (порт 8000) — админ-панель (`/admin/`)
- **PostgreSQL 18** — база данных

## Требования

- Docker и Docker Compose

## Запуск с нуля

```bash
git clone <URL> stafftracker-back
cd stafftracker-back
```

```bash
cp .env.example .env
```

```bash
make run
```

Готово. Через ~30 секунд будут доступны:

- **API** — http://localhost:8001/docs (Swagger UI)
- **Django Admin** — http://localhost:8000/admin/

Логин в Django Admin: `admin` / `admin`

## Первая Alembic-миграция

При первом запуске нужно сгенерировать и применить миграцию для бизнес-таблиц:

```bash
make migration msg="initial"
make migrate
```

После этого перезапустить Django, чтобы он увидел таблицы:

```bash
make restart
```

## Команды Makefile

| Команда | Описание |
|---|---|
| `make run` | Поднять все контейнеры |
| `make stop` | Остановить все контейнеры |
| `make restart` | Перезапуск |
| `make build` | Собрать образы без запуска |
| `make status` | Статус контейнеров |
| `make migration msg="описание"` | Сгенерировать Alembic-миграцию |
| `make migrate` | Применить Alembic-миграции |
| `make shell-django` | Django shell |
| `make shell-api` | Bash в API контейнере |
| `make createsuperuser` | Создать суперпользователя вручную |
| `make clean` | Удалить контейнеры, volumes и образы |

## Переменные окружения

Все настройки в файле `.env`:

| Переменная | По умолчанию | Описание |
|---|---|---|
| `DEBUG` | `True` | Режим отладки |
| `SECRET_KEY` | `dev-secret-key...` | Секрет Django |
| `POSTGRES_DB` | `stafftracker` | Имя БД |
| `POSTGRES_USER` | `stafftracker` | Пользователь БД |
| `POSTGRES_PASSWORD` | `stafftracker` | Пароль БД |
| `DATABASE_URL` | `postgresql+asyncpg://...` | URL для SQLAlchemy |
| `DJANGO_SUPERUSER_USERNAME` | `admin` | Логин суперпользователя |
| `DJANGO_SUPERUSER_PASSWORD` | `admin` | Пароль суперпользователя |

## Архитектура

```
FastAPI (api, :8001)          Django (admin, :8000)
   |                               |
   | SQLAlchemy async              | Django ORM (managed=False)
   | Alembic миграции              | Только чтение таблиц
   |                               |
   +----------- PostgreSQL 18 -----+
```

- SQLAlchemy владеет схемой БД, Alembic управляет миграциями
- Django использует `managed=False` модели для отображения данных в админке
- Django `migrate` создаёт только свои служебные таблицы (`auth_user` и т.д.)
