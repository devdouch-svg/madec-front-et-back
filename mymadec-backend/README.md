# My Madec — Backend API

FastAPI backend for the My Madec B2B ordering platform.

> **New contributor?** See **[DEVELOPER_ONBOARDING.md](./DEVELOPER_ONBOARDING.md)** for full setup: SQL Server Express, ODBC, Alembic migrations, frontend, and demo accounts.

## Stack

| Layer | Technology |
|---|---|
| Framework | FastAPI 0.111 |
| Database | Microsoft SQL Server (MsSQL) via pyodbc + SQLAlchemy 2 |
| Migrations | Alembic |
| Auth | JWT (access + refresh tokens) · bcrypt |
| Push | Firebase Cloud Messaging (FCM) |
| Email | SMTP |
| Rate limiting | slowapi |
| Containerisation | Docker + docker-compose |

---

## Quick start (Docker)

```bash
cp .env.example .env          # fill in DB_PASSWORD, SMTP_*, etc.
docker-compose up --build
```

API available at: http://localhost:8000  
Swagger UI (dev only): http://localhost:8000/docs

---

## Local setup (without Docker)

Use **Python 3.11 or 3.12**. Python **3.14 is not supported** (`pydantic==2.8.2` has no 3.14 wheel).

**Windows (recommended):**

```powershell
.\setup.ps1
.\.venv\Scripts\Activate.ps1
```

**Manual:**

```bash
py -3.12 -m venv .venv          # do not use default python if it is 3.14
# Linux/macOS: python3.12 -m venv .venv && source .venv/bin/activate
.\.venv\Scripts\Activate.ps1  # Windows
pip install -r requirements.txt
cp .env.example .env           # configure .env
```

### Run migrations

```bash
alembic upgrade head
```

### Start the server

```bash
uvicorn app.main:app --reload
```

---

## Roles

| Role | Description |
|---|---|
| `admin` | Full access |
| `gestionnaire` | Manage orders + view users |
| `acheteur` | Place orders, view own orders + catalogue |
| `service` | ETL service account (static bearer token) |

---

## Environment variables

See [`.env.example`](.env.example) for all available options.

Critical ones:

```
SECRET_KEY          — JWT signing key (change in production!)
DB_HOST / DB_NAME   — MsSQL connection
SMTP_HOST / SMTP_USER / SMTP_PASSWORD
FIREBASE_CREDENTIALS_PATH
```

---

## API Routes

### Auth
| Method | Path | Auth |
|---|---|---|
| POST | `/api/v1/auth/login` | public |
| POST | `/api/v1/auth/logout` | JWT |
| POST | `/api/v1/auth/refresh` | public |
| POST | `/api/v1/auth/reset-password/request` | public |
| POST | `/api/v1/auth/reset-password/confirm` | public |

### Users
| Method | Path | Auth |
|---|---|---|
| GET | `/api/v1/users` | admin/gestionnaire |
| POST | `/api/v1/users` | admin |
| GET | `/api/v1/users/me` | any |
| PUT | `/api/v1/users/me` | any |
| GET | `/api/v1/users/me/plafond` | any |
| GET/PUT/PATCH | `/api/v1/users/{id}/*` | admin |

### Products, Orders, Sync, Banners, Notifications
See Swagger UI at `/docs` (dev mode).

---

## Running tests

```bash
pytest tests/ -v
```

Tests use SQLite in-memory — no SQL Server required.

---

## Project structure

```
app/
├── api/v1/         # Route handlers
├── core/           # Config, security, dependencies, exceptions
├── db/             # SQLAlchemy engine + seeder
├── models/         # ORM models
├── schemas/        # Pydantic request/response schemas
└── services/       # Business logic
alembic/            # Database migrations
tests/              # pytest test suite
uploads/            # Product images + banner images (gitignored)
```
