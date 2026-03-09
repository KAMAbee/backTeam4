# Quick Deploy (готовые решения)

## 1) Render (самый простой)
1. Залей репозиторий в GitHub.
2. В Render выбери `New +` -> `Blueprint`.
3. Укажи репозиторий: Render сам прочитает `render.yaml`.
4. Нажми Deploy.

Что создастся автоматически:
- Web service (Docker)
- PostgreSQL
- ENV-переменные (включая `DATABASE_URL`, `SECRET_KEY`)

После первого деплоя:
- Swagger: `https://<your-app>.onrender.com/api/docs/`
- Admin: `https://<your-app>.onrender.com/admin/`

## 2) Railway (через Dockerfile)
1. `New Project` -> `Deploy from GitHub Repo`.
2. Добавь PostgreSQL plugin.
3. В Variables укажи:
   - `DEBUG=False`
   - `SECRET_KEY=<strong_secret>`
   - `ALLOWED_HOSTS=*` (или домен)
   - `DATABASE_URL=${{Postgres.DATABASE_URL}}`
   - при необходимости: `CORS_ALLOW_ALL_ORIGINS=True`
4. Deploy: Railway соберет контейнер из `Dockerfile`.

## Важно
- Приложение стартует через `entrypoint.sh`:
  - `migrate`
  - `collectstatic`
  - `gunicorn`
- Поддерживаются оба режима БД:
  - через `DATABASE_URL` (PaaS)
  - через `DB_NAME/DB_USER/DB_PASSWORD/DB_HOST/DB_PORT` (локально/VPS)
