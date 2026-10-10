# DIOS Knowledge — backend

Корпоративная база знаний: пространства, коллекции, статьи с историей редакций, ACL и гибридный поиск (dense + BM25) по опубликованным материалам.

- Продукт: [`docs/product/vision.md`](docs/product/vision.md)
- Архитектура: [`.agents/architecture.md`](.agents/architecture.md), решения — [`docs/architecture/decisions.md`](docs/architecture/decisions.md), поиск — [`docs/architecture/search.md`](docs/architecture/search.md)

## Запуск для разработки

Нужны Python 3.14, [uv](https://docs.astral.sh/uv/), Docker и запущенный DIOS (IAM и Media Service, по умолчанию `http://localhost:8001`).

```bash
cp .env.example .env            # заполнить AITUNNEL_API_KEY и SRV_MEDIA_CLIENT_SECRET
docker compose up -d            # PostgreSQL 18, Qdrant, RabbitMQ (docker/*.docker-compose.yml)
uv sync
uv run alembic upgrade head
```

Процессы (каждый в своём терминале):

```bash
uv run uvicorn src.main:app --port 8010                               # API, Swagger: http://localhost:8010/docs
uv run taskiq worker src.infra.broker.tasks:broker                    # индексация статей
uv run python -m src.infra.outbox.relay                               # outbox → очередь индексации
```

Проверки:

```bash
uv run ruff check src tests migrations
uv run pytest
```

## Быстрый сценарий

1. Получить токен DIOS: `POST http://localhost:8001/api/v1/auth/login` (`admin@admin.com` / `admin`).
2. Админ создаёт пространство: `POST /api/admin/v1/spaces` (`organizationWide: true` — READ для всей организации).
3. Админ выдаёт права роли: `POST /api/admin/v1/access/grants`
   `{"resource": {"type": "space", "id": "..."}, "subject": {"type": "role", "id": "support_agent"}, "permissions": ["READ", "WRITE", "PUBLISH"]}`.
4. Пользователь создаёт статью `POST /api/user/v1/spaces/{spaceId}/articles` и публикует `POST /api/user/v1/articles/{id}/publish {"revisionId": ...}`.
5. Через пару секунд статья ищется: `POST /api/user/v1/search {"query": "..."}`.
