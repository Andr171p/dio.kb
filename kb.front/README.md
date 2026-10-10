# DIOS Knowledge — frontend

Веб-интерфейс базы знаний: пространства и коллекции, чтение статей, редактор с историей редакций, публикация, поиск по смыслу. Правила разработки — [`.agents/AGENTS.md`](.agents/AGENTS.md), палитра — [`.agents/design.md`](.agents/design.md).

## Запуск

Нужны Node 22+, запущенный DIOS (IAM и Media Service на `:8001`) и backend базы знаний на `:8010` (см. [`../kb.back/README.md`](../kb.back/README.md)).

```bash
cp .env.example .env
npm install
npm run dev        # http://127.0.0.1:5174, вход учётной записью DIOS
```

В dev запросы идут через proxy Vite (`/auth-api` → DIOS, `/kb-api` → Knowledge), поэтому CORS на backend не нужен.

Проверки: `npm run typecheck`, `npm run lint`, `npm test`, `npm run build`.

## Стек и решения

- React 19, TypeScript, Vite, SCSS Modules, Zustand, React Router 8 (адреса статей и поиска можно отправить ссылкой).
- FSD: `app → pages → widgets → features → entities → shared`, границы проверяет ESLint. Алиасы по слоям: `@entities/...`, `@shared/...`.
- Запросы — через `BackendCaller` из `shared/api` прямо из stores/features, без отдельного API-слоя.
- Авторизация — свой экран входа через IAM DIOS: access-токен только в памяти, refresh ротируется в localStorage, вкладки синхронизируются.
- Права (`READ/WRITE/PUBLISH/ARCHIVE`) приходят с backend в ответах; UI только скрывает действия, проверяет сервер.
- Редактор — TipTap v3 + `@tiptap/markdown`: Markdown остаётся каноническим форматом. Таблицы, чеклисты, блоки кода с выбором языка (в том числе 1С и PowerShell), изображения через Media Service (`media://<id>`), меню блоков по «/», плавающая панель форматирования, перетаскивание блоков. Сохранение создаёт новую редакцию; конфликт (409) не теряет текст.
- Просмотр — `react-markdown` без исполнения HTML; якоря заголовков совпадают с якорями поиска. Ссылки на статьи, заявки DIOS и внешние сайты показывают превью (внешние — через `GET /api/user/v1/link-preview`); ссылка отдельным абзацем отображается карточкой.
- Стекло (glassmorphism) — только у навигации, глобального поиска (⌘/Ctrl+K) и плавающих панелей редактора. Текст статьи, таблицы, код и выдача поиска — на непрозрачных поверхностях.
- Шрифты: JetBrains Mono — интерфейс и заголовки, Inter — текст статей.

## Известные ограничения

- Media Service не знает тип владельца «статья»: изображения загружаются от имени пользователя (`owner_type=user`).
- Импорт/экспорт DOCX/PDF на backend пока нет; доступна печать статьи в PDF средствами браузера.
- В IAM нет поиска пользователей: при выдаче доступа список ограничен первой сотней.
