# Поиск: индексация и безопасная выдача

PostgreSQL (опубликованная редакция) — источник истины; Qdrant — восстанавливаемая проекция.

## Индексация

```text
publish / unpublish / archive → Article + outbox_messages (одна транзакция)
→ outbox relay → RabbitMQ (Taskiq) → sync_article_index(article_id)
→ worker читает актуальное состояние в PostgreSQL:
    не опубликована / в архиве → удалить фрагменты статьи
    опубликована (редакция R):
      Markdown AST → блоки с путём заголовков
      → media:// изображения → vision-модель: OCR + описание за один вызов (кеш image_texts)
      → фрагменты по секциям ≤ 1600 символов (таблицы/код не режутся; большие таблицы — с повтором шапки)
      → dense-эмбеддинги только для изменившихся фрагментов (по content_hash из Qdrant)
      → advisory lock(article) → перечитать: published_revision_id всё ещё R?
      → upsert фрагментов R, удалить фрагменты прочих редакций → article_index_states
```

- Задача **идемпотентна** и не доверяет содержимому события: дубли и переупорядоченные доставки безопасны. Если за время OCR/эмбеддингов публикация изменилась, задача выходит — следующую синхронизацию уже поставило новое событие.
- Сбой одного изображения не прерывает индексацию: текст индексируется, id изображения пишется в `article_index_states.failed_media_ids`.
- Текст для поиска фрагмента: `Заголовок статьи › H1 › H2` + фрагмент + распознанный текст и описание изображений. В ответе отдаётся только исходный Markdown фрагмента и якорь раздела (GitHub-style slug, дубли — `-1`, `-2`).

## Коллекция Qdrant

`kb_chunks_g{generation}` (`QDRANT_GENERATION`):

| Вектор | Назначение |
|---|---|
| `dense` | эмбеддинг AI Tunnel (`AITUNNEL_EMBEDDING_MODEL`, cosine) |
| `bm25` | sparse BM25 с IDF, **считается сервером Qdrant** (`qdrant/bm25`, `language: russian`) |

Токенизатор BM25 — по умолчанию (`word`): с `multilingual` русский стемминг не применяется (проверено на 1.19).

Payload: `organization_id` (tenant-индекс), `space_id`, `article_id`, `revision_id`, `position`, `heading_path`, `anchor`, `text`, `content_hash`, `media_ids`. ID точки — `uuid5(article_id, "{revision_id}:{position}")`.

**Смена модели эмбеддингов, размерности или парсера** → увеличить `QDRANT_GENERATION`, перезапустить API/worker (создастся новая коллекция) и вызвать `POST /api/admin/v1/search/reconcile`. Пока новая коллекция наполняется, поиск по ней неполный; переключение по алиасу (blue/green) — следующий шаг, когда понадобится.

## Запрос

`POST /api/user/v1/search {query, spaceIds?, limit}`:

1. `resolve_search_scope`: Space с `READ` и статьи с прямым `READ` по grants субъектов пользователя. Пустая область → пустой ответ **без запроса в Qdrant**.
2. Qdrant Query API: prefetch `dense` и prefetch `bm25` с фильтром `organization AND (space ∈ scope OR article ∈ scope) [AND space ∈ spaceIds]` → слияние RRF → группировка по `article_id` (до 3 фрагментов на статью) с двукратным запасом.
3. Пакетная сверка с PostgreSQL до выдачи текста: организация, статья не в архиве, Space активен, `revision_id` фрагмента = актуальная `published_revision_id`, статья в области.
4. Ответ — статьи (заголовок опубликованной редакции, slug, Space) с фрагментами и якорями.

Порога релевантности нет: в небольшом корпусе выдаются все статьи из области, упорядоченные по RRF. Reranker (после проверки прав) подключается отдельным портом, когда появится корпус запросов для измерений.

## Порты

| Порт (`application/search`) | Реализация |
|---|---|
| `SearchChunkRepository` | `infra/qdrant/repository.py` |
| `TextEmbedder` | `infra/ai/embedder.py` (OpenAI-клиент → AI Tunnel) |
| `ImageTextExtractor` | `infra/ai/image_extractor.py` (vision, JSON-ответ) |
| `MediaStorage` | `SrvMediaClient.download` (presigned URL Media Service) |
| `IndexingQueue` | `TaskiqIndexingQueue` |
| `ImageTextRepository`, `ArticleIndexStateRepository` | PostgreSQL |

## Сверка

`article_index_states` хранит, какая редакция и в каком индексе лежит. `POST /api/admin/v1/search/reconcile` ставит в очередь статьи, у которых опубликованная редакция расходится с проиндексированной (или индекс сменился); `POST /api/admin/v1/search/articles/{id}/sync` — переиндексация одной статьи. Если индекс потерян или пересоздан вне приложения — `reconcile?full=true`.
