# AI Answers / Knowledge Gaps — решения для backend-реализации

> **Статус:** Accepted (итерации A + B)  
> **Дата:** 21 ноября 2026 г.  
> **Контекст:** реализация по `DIOS_KB_AI_ANSWERS_KNOWLEDGE_GAPS_IMPLEMENTATION.md`, пока только backend.

## Согласованный scope — итерация A

| Включено | Отложено |
|---|---|
| DTOs, evidence, citations, `answer_question` | Knowledge Gaps (Phase 4) |
| `answer_runs` + store (claim/lease) + Alembic | AI-assisted authoring (Phase 5) |
| Taskiq + outbox enqueue generate | Durable progress event log |
| LLM structured generation через AI Tunnel | Cancel endpoint |
| SSE progress (snapshot + heartbeat) | Claim-level faithfulness |
| `POST/GET /answers`, feedback `PUT` | Rate limiter / cost dashboards |
| Redis (docker + optional notifier) | Frontend / Next.js |
| Unit + store/API tests | |

---

## Принятые решения

### 1. Scope
**Accepted:** сначала только AI Answers; Gaps — следующей итерацией.

### 2. API surface
**Accepted:** оба роутера — `/api/user/v1/answers` и `/api/service/v1/answers`.  
Отличие: auth-зависимость роутера (`CurrentUser` vs client gate + user) и дублирование тонких endpoints; use cases общие.

### 3. Auth во worker и повторная проверка прав
**Accepted:** права **перепроверяются** по актуальному состоянию ACL (PostgreSQL), потому что grants могут отозвать.

Практическая схема MVP:

1. В `AnswerRun` храним `principal_id`, `principal_type`, `organization_id` (и при необходимости snapshot ролей только как hint для search scope).
2. Worker при retrieval/validation и API при `GET`/`feedback` опираются на **текущие** AccessGrants / `find_readable_published`, а не на «замороженный» набор статей из момента `POST`.
3. Если во время generation доступ к источникам пропал → `FAILED` + `ACCESS_CHANGED`, без выдачи текста.
4. На `GET` завершённого ответа — повторная проверка читаемости сохранённых sources; при отказе — безопасный отказ без цитат.

Полный re-fetch membership/ролей из IAM (если появится trusted service API) — улучшение поверх этой схемы; до него subjects строятся из trusted `user_id` + `organization_id` (+ публичный subject), а авторитет — KB grants в PostgreSQL.

### 4. Progress / Redis
**Accepted:** добавить Redis по шаблону остальных docker-сервисов проекта.  
PostgreSQL snapshot — source of truth; Redis Pub/Sub — уведомления после commit.  
Для single-instance/dev допустим fallback `memory`, но Redis в compose присутствует.

### 5. Privacy
**Accepted:** default `full` (`ANSWERS_PRIVACY_MODE`). Retention/scrub — позже.

### 6. URL источников
**Accepted (временно):** `/spaces/{space_id}/articles/{slug}#{anchor}` (hash опционален).  
Формирование вынесено в одну функцию/`BuildSourceUrl`, чтобы сменить формат без правки пайплайна.

### 7. LLM / AI Tunnel
**Accepted:** конфиг из `.env` / `AITUNNEL_*`. Для разработки — дешёвые модели, экономный лимит токенов (`ANSWERS_*` + отдельная `AITUNNEL_ANSWER_MODEL`).

### 8. Knowledge Gaps grants
**Accepted (итерация B, MVP):** без отдельных `knowledge_gap:*` Permission flags.

- Список/карточка: `auth.is_admin` **или** `WRITE` на `space_id` gap (если задан).
- Gaps без `space_id` (org triage): только `admin`.
- Mutation (triage/assign/start/resolve/dismiss/reopen): те же правила.
- Отдельные grants `knowledge_gap:*` — после согласования с моделью AccessGrants.

### 9. Прочее (без возражений)
- Outbox: application message `GenerateAnswer` (без domain aggregate) + relay → Taskiq; payload задачи — `run_id`.
- Idempotency-Key на `POST` — да.
- Cancel — нет в A.

---

## Итерация B — Knowledge Gaps (Accepted)

| Включено | Не включено |
|---|---|
| Domain `KnowledgeGap` aggregate | AI-assisted authoring |
| `gap_signals` + idempotent record | Semantic clustering / embeddings |
| Signals из AnswerRun + negative feedback | LLM classification |
| Rule-based batch detection + upsert | Search telemetry signals |
| Editorial API user+service | Отдельные Permission flags |
| Taskiq detect task (+ optional manual trigger) | Frontend inbox |

**Detection MVP:**

1. Пишем signal при `COMPLETED` + `insufficient_evidence` / `conflicting_evidence` и при thumbs-down feedback.
2. **Не** пишем signal на `FAILED` / timeout / `ACCESS_CHANGED`.
3. Группировка: детерминированный `grouping_key` = hash(kind + нормализованный topic_hint).
4. Один signal уже может создать `NEEDS_TRIAGE` candidate (порог `GAPS_MIN_SIGNALS`, default 1 для пилота).
5. `MISSING_CONTENT` не назначаем автоматически только по `insufficient_evidence`.

---

## Чеклист

- [x] Scope: только A (Answers+SSE+Feedback)
- [x] API: user + service
- [x] Worker/API: повторная проверка актуальных прав
- [x] Redis в docker по шаблону проекта
- [x] Privacy: full
- [x] Source URL формат (сменный)
- [x] Cheap models / .env для AI Tunnel
- [x] Gaps — iteration B
- [x] Gaps auth MVP: admin / space WRITE
