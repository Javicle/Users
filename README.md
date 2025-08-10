## Users Service (FastAPI)

Микросервис управления пользователями: создание, получение, обновление, удаление и базовая проверка учетных данных. Построен на FastAPI, SQLAlchemy (async) и внутренних библиотеках OpenVerse.

### Возможности

- **Создание пользователя** по данным `login/name/email/password`.
- **Получение пользователя** по `id` или `login`.
- **Обновление пользователя** по `login` (имя, e-mail, пароль, активность).
- **Удаление пользователя** по `id` или `login`.
- **Список всех пользователей**.
- **Проверка учетных данных (логин)** — возвращает пользователя при валидной паре `login/password`.
- **Готовность к трассировке** (Jaeger) и логированию; простой `health`-чек.

## Архитектура и зависимости

- **Веб-фреймворк**: `FastAPI`
- **ORM**: `SQLAlchemy 2.x` (async, `asyncpg` | `aiosqlite`)
- **Сервер**: `uvicorn`
- **Типизация/валидация**: `Pydantic v2`
- **Кэш/фон**: `redis` (опционально)
- **Внутренние пакеты**:
  - `tools-openverse` — конфигурация, логгер, утилиты, формы
  - `app-starter` — менеджер приложения, Jaeger/OTel

Ключевые модули:

- `src/main.py` — создание приложения, регистрация роутов, инициализация БД, Jaeger
- `src/delivery/route/user.py` — HTTP-маршруты
- `src/usecases/user.py` — бизнес-логика пользователей
- `src/infra/repository/user/user.py` — репозиторий и доступ к БД
- `src/infra/repository/db/base.py` — инициализация движка/сессий и автосоздание таблиц
- `src/infra/repository/db/models/user.py` — модель БД `users`
- `src/entities/user/*` — доменные сущности/DTO/исключения/валидаторы

## Требования

- Python 3.12+
- База данных: PostgreSQL (рекомендуется) или SQLite для локальной разработки
- Poetry (рекомендуется)

## Переменные окружения

Загружаются через `tools_openverse.common.config.settings`.

- `PROJECT_NAME` — имя сервиса (используется при старте и трассировке)
- `BASE_URL` — host для запуска (например, `0.0.0.0`)
- `PORT_SERVICE_USERS` — порт сервиса (например, `8080`)
- `DATABASE_URL` — строка подключения к БД в формате SQLAlchemy (async):
  - PostgreSQL: `postgresql+asyncpg://user:password@host:5432/dbname`
  - SQLite (локально): `sqlite+aiosqlite:///db.sqlite3`
- (опц.) `REDIS_HOST`, `REDIS_PORT`, `REDIS_DB`, `REDIS_PASSWORD` — настройки Redis

Пример `.env`:

```env
PROJECT_NAME=user_service
BASE_URL=0.0.0.0
PORT_SERVICE_USERS=8080
DATABASE_URL=sqlite+aiosqlite:///db.sqlite3

# Опционально Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=
```

## Установка и запуск (Poetry)

```bash
# 1) Установить Poetry (если не установлен)
# https://python-poetry.org/docs/

# 2) Установить зависимости
poetry install

# 3) Запустить сервис
poetry run python src/main.py
```

После старта OpenAPI-документация будет доступна по адресу: `http://<BASE_URL>:<PORT_SERVICE_USERS>/docs`.

Альтернатива (без Poetry):

```bash
python -m venv .venv
. .venv/Scripts/activate  # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install fastapi uvicorn sqlalchemy asyncpg aiosqlite pydantic pydantic-settings redis python-multipart
pip install git+https://github.com/Javicle/_ToolsOpenVerse.git git+https://github.com/Javicle/_AppStarter
python src/main.py
```

## База данных и миграции

- Таблицы создаются автоматически при старте (см. `src/infra/repository/db/base.py::init_db`).
- Модель пользователя: `src/infra/repository/db/models/user.py`
  - Таблица: `users`
  - Поля: `id: UUID (PK)`, `login: str (unique)`, `name: str`, `email: str (unique)`, `password: str`, `is_active: bool`, `created_at: datetime`, `updated_at: datetime`
  - Примечание (PostgreSQL): используется `server_default text("gen_random_uuid()")`. Убедитесь, что доступна функция `gen_random_uuid()` (расширение `pgcrypto`), или полагайтесь на генерируемый приложением `uuid4`.

## Маршруты API

Базовые роуты регистрируются в `src/delivery/route/user.py`.

### POST /users/create

- Назначение: создать пользователя
- Тело запроса (JSON):
  ```json
  {
    "login": "demo_user",
    "name": "Demo",
    "email": "demo@example.com",
    "password": "S3cure!Pass"
  }
  ```
- Ответ: `201 Created`, тело — `UserResponseDTO`

### GET /users/get/{user_id}

- Назначение: получить пользователя по UUID
- Ответ: `UserResponseDTO`

### GET /users/login/{user_login}

- Назначение: получить пользователя по логину
- Ответ: `UserResponseDTO`

### PUT /users/update

- Назначение: обновить данные пользователя по `login`
- Тело запроса (JSON, любые поля опциональны):
  ```json
  {
    "login": "demo_user",
    "name": "Demo Updated",
    "email": "demo_new@example.com",
    "password": "N3w!Pass",
    "is_active": true
  }
  ```
- Ответ: `200 OK`, тело — `UserResponseDTO`

### DELETE /users/delete/{user_id}

- Назначение: удалить пользователя по UUID
- Ответ: `204 No Content`

### DELETE /users/delete/login/{user_login}

- Назначение: удалить пользователя по логину
- Ответ: `204 No Content`

### GET /users/get_all

- Назначение: получить список всех пользователей
- Ответ: `200 OK`, массив `UserResponseDTO`

### POST /users/log_in

- Назначение: базовая проверка учетных данных (вернет пользователя при валидной паре `login/password`)
- Вход: `application/x-www-form-urlencoded` с полями `login`, `password`
- Ответ: `200 OK`, тело — `UserResponseDTO` (при неверных данных — ошибки ниже)

### GET /health

- Назначение: health-check сервиса
- Ответ: `{ "status": "OK" }`

## Примеры запросов

```bash
# Создать пользователя
curl -X POST "http://localhost:8080/users/create" \
     -H "Content-Type: application/json" \
     -d '{"login":"demo","name":"Demo","email":"demo@example.com","password":"S3cure!Pass"}'

# Получить по ID
curl -X GET "http://localhost:8080/users/get/<UUID>"

# Получить по логину
curl -X GET "http://localhost:8080/users/login/demo"

# Обновить
curl -X PUT "http://localhost:8080/users/update" \
     -H "Content-Type: application/json" \
     -d '{"login":"demo","name":"Demo Updated"}'

# Удалить по ID
curl -X DELETE "http://localhost:8080/users/delete/<UUID>"

# Удалить по логину
curl -X DELETE "http://localhost:8080/users/delete/login/demo"

# Все пользователи
curl -X GET "http://localhost:8080/users/get_all"

# Логин (проверка учетных данных)
curl -X POST "http://localhost:8080/users/log_in" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "login=demo&password=S3cure!Pass"
```

## Коды ошибок (основные)

- `400 Bad Request` — ошибки валидации/некорректный запрос
- `401 Unauthorized` — неверные учетные данные при `/users/log_in`
- `404 Not Found` — пользователь не найден (в некоторых случаях возвращается как `400` с текстом ошибки)
- `500 Internal Server Error` — внутренняя ошибка сервиса

## Логирование и трассировка

- Логи: через `tools_openverse.setup_logger`, вывод в консоль/файлы согласно настройкам окружения
- Трассировка: при старте включается `JaegerService` (см. `src/main.py`). Необходимые параметры читаются через `settings` (`app-starter`)

## Структура проекта (сокр.)

```
user_service/
  src/
    delivery/route/user.py                 # HTTP-роуты
    usecases/user.py                       # Бизнес-логика
    infra/repository/db/base.py            # Инициализация БД (engine/session, create_all)
    infra/repository/db/models/user.py     # Модель таблицы users
    infra/repository/user/user.py          # Репозиторий (CRUD, логин)
    entities/user/{dto,entity,exc,...}.py  # Доменные объекты и DTO
    main.py                                # Точка входа
```

## Разработка

- Форматирование: `black`, `isort`
- Линтинг: `flake8` (по желанию), типизация: `mypy`
- Тесты: `pytest`

Команды (через Poetry):

```bash
poetry run black .
poetry run isort .
poetry run mypy
poetry run pytest -q
```

## Заметки и ограничения

- Пароли сейчас хранятся в открытом виде (для демо). Для продакшена обязательно добавьте хеширование (например, `bcrypt`) и политику смены пароля.
- Миграции Alembic отсутствуют — для продакшена рекомендуется их добавить.
- Для PostgreSQL удостоверьтесь, что доступна `gen_random_uuid()` (или удалите `server_default` и генерируйте UUID на стороне приложения).
- Эндпоинт `/users/log_in` только проверяет учетные данные и возвращает пользователя. Выдача токенов — зона ответственности отдельного Auth-сервиса.

## Лицензия

MIT или по договоренности владельца репозитория.
