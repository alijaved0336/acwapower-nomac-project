# ACWA Power – NOMAC (SWRO Analytics Platform)

Source-structure sample of a desalination (SWRO) plant analytics and dashboard platform.
This repo shows how the codebase is organised; it is **not** a runnable deployment (secrets, data and build output are stripped).

## Repository layout

```
backend/      Django REST API (Python) – dashboards, auth, roles, data-lake access
frontend/     Next.js web app (React + TypeScript) – dashboards and admin UI
migrations/   One-off data migration script (Databricks Hive Metastore -> Azure Data Lake)
```

## Technologies

| Layer | Stack |
|-------|-------|
| Frontend | Next.js (App Router), React 19, TypeScript, Ant Design + MUI, Redux Toolkit, TanStack Query, Axios, ECharts / Chart.js / ApexCharts, Leaflet, Tailwind/PostCSS, Jest, Husky |
| Auth | Azure AD via MSAL (`@azure/msal-*`) and `next-auth` on the frontend; JWT (PyJWT) validated by the backend |
| Backend | Python 3.12, Django 5 + Django REST Framework, drf-yasg (Swagger), Gunicorn, WhiteNoise, django-cors-headers |
| Data | PySpark + Delta Lake / `deltalake`, PyArrow, Azure Data Lake Storage (ADLS), ClickHouse, Databricks SQL connector |
| Caching / jobs | Redis (`django-redis`), APScheduler |
| DevOps | Docker, Azure Pipelines (`azure-pipelines.yml`), Azure App Service (`startup.sh`, `.deployment`), pre-commit, black/flake8/isort |

## How the code flows

1. **Login** – the browser signs the user in through Azure AD (MSAL). The frontend keeps the token and attaches it to every API call through the Axios client in `frontend/src/services`.
2. **Page render** – routes live in `frontend/src/app` (`(auth)` for login, `(dashboard)` for the dashboards). Each dashboard page calls a hook in `src/hooks`, which uses TanStack Query + Redux (`src/store`) to fetch and cache data, then renders chart components from `src/components`.
3. **API entry** – requests hit Django URLs in `backend/interface/v1`. `interface/` is the HTTP-facing layer: serializers, schemas and repository interfaces.
4. **Business logic** – `backend/infrastructure/controllers/<dash_xxx>` hold one controller per dashboard/widget (permissions, roles, column schema, analysis…). They call `infrastructure/services` (auth, cache, ClickHouse, ADLS, analysis) and `infrastructure/orm` (Django models + repositories).
5. **Data access** – heavy analytical reads go to ClickHouse or to Delta tables in ADLS through Spark/PyArrow; results are cached in Redis and returned as JSON. A scheduler (APScheduler) and an ADLS listener keep ClickHouse in sync when new files land in the lake.
6. **Migration utility** – `migrations/hms_to_adls.py` copies tables from Databricks into ADLS in a per-site folder layout (`swro/tables/gold/<site>/`).
7. **Deploy** – Azure Pipelines build the backend and frontend separately and deploy to Azure App Service.

## Running locally (reference)

Backend: Python 3.12 + Java 8+ (Spark) -> `pip install -r requirements.txt` -> copy env vars -> `python manage.py runserver`.
Frontend: Node + pnpm -> `pnpm install` -> `pnpm dev`.
Environment variables are not included; create your own `.env` files.
