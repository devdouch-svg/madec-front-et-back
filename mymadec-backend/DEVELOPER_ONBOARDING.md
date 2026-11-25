# My Madec — Developer onboarding guide

This document is for developers who will contribute to **My Madec** (B2B ordering platform). It covers what to install, how to configure **Microsoft SQL Server**, how to run **migrations**, and how to start the **backend** and **frontend** locally.

**Repository:** https://github.com/mohamedtaqysalmi/my-madec  

The Git repository contains only:

| Folder       | Stack                                      |
|-------------|---------------------------------------------|
| `backend/`  | Python 3.11+, FastAPI, SQLAlchemy, Alembic |
| `frontend/` | Node.js 20+, React, TypeScript, Vite       |

Do **not** commit `venv/`, `node_modules/`, or `.env` files (they are ignored).

---

## 1. Prerequisites (install once)

### Required for everyone

| Tool | Version | Notes |
|------|---------|--------|
| **Git** | Latest | Clone the repo |
| **Python** | **3.11 or 3.12** (required). Do **not** use 3.14 — `pip install -r requirements.txt` fails. | Backend API |
| **Node.js** | 20 LTS or newer | Includes `npm` — frontend |
| **Microsoft SQL Server** | Express or Developer edition | Application database |
| **ODBC Driver for SQL Server** | **17** or **18** (prefer **18**) | Required by `pyodbc` |

### Optional (recommended)

| Tool | Use |
|------|-----|
| **Docker Desktop** | Run SQL Server in a container instead of local Express |
| **SQL Server Management Studio (SSMS)** | Create database, run SQL, inspect data |
| **VS Code / Cursor** | Editor |

### Not required for basic backend work

- **Firebase** — only for push notifications (FCM); app works without it locally  
- **SMTP** — password-reset emails; set `DISABLE_EMAIL=true` in dev  

---

## 2. Clone the project

```powershell
git clone https://github.com/mohamedtaqysalmi/my-madec.git
cd my-madec
```

You should see `backend/` and `frontend/` at the root.

---

## 3. Database setup

The backend uses **Microsoft SQL Server** (not PostgreSQL/MySQL). Choose **one** of the options below.

### Option A — SQL Server Express on Windows (typical for local dev)

1. **Download & install SQL Server Express**  
   - https://www.microsoft.com/en-us/sql-server/sql-server-downloads  
   - Choose **Express** (free).  
   - During setup, note the instance name (often `SQLEXPRESS`).

2. **Install SQL Server Management Studio (SSMS)** (optional but useful)  
   - https://learn.microsoft.com/en-us/sql/ssms/download-sql-server-management-studio-ssms  

3. **Install ODBC Driver 18 for SQL Server**  
   - https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server  
   - Verify in **Windows → ODBC Data Sources (64-bit) → Drivers** that you see  
     `ODBC Driver 18 for SQL Server`.

4. **Enable SQL Server Authentication** (if you use `sa` + password)  
   - In SSMS: connect → right-click server → **Properties** → **Security** →  
     **SQL Server and Windows Authentication mode** → restart SQL Server service.

5. **Create the application database**

   In SSMS, run:

   ```sql
   CREATE DATABASE mymadec;
   ```

6. **Connection settings for `.env`**

   **Named instance (Express default):**

   ```env
   DB_HOST=localhost\SQLEXPRESS
   DB_NAME=mymadec
   DB_DRIVER=ODBC Driver 18 for SQL Server
   ```

   **Windows Authentication** (no SQL login — leave user/password empty):

   ```env
   DB_USER=
   DB_PASSWORD=
   ```

   **SQL login (`sa` or dedicated user):**

   ```env
   DB_USER=sa
   DB_PASSWORD=YourStrongPasswordHere
   ```

   The app adds `TrustServerCertificate=yes` automatically for local Express (required with ODBC Driver 18).

7. **TCP/IP** (only if connection fails)  
   - Open **SQL Server Configuration Manager** → **SQL Server Network Configuration** →  
     **Protocols for SQLEXPRESS** → enable **TCP/IP** → restart service.  
   - Default port: **1433** (not used for named-instance connections the same way; `localhost\SQLEXPRESS` is enough).

---

### Option B — SQL Server via Docker (no local Express install)

From the `backend/` folder:

```powershell
cd backend
copy .env.example .env
# Set DB_PASSWORD in .env to match docker-compose (default: DevPassword123!)
docker compose up -d db
```

Wait until the container is healthy (~30–60 s first time), then use:

```env
DB_HOST=localhost
DB_PORT=1433
DB_NAME=mymadec
DB_USER=sa
DB_PASSWORD=DevPassword123!
DB_DRIVER=ODBC Driver 18 for SQL Server
```

Create the database (once) with `sqlcmd` or SSMS connected to `localhost,1433`:

```sql
CREATE DATABASE mymadec;
```

> **Note:** On Windows, you still need the **ODBC driver** installed on the host to run the API outside Docker.

---

## 4. Backend setup

```powershell
cd backend

# Virtual environment (must be 3.12, not default 3.14)
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
# Or from this folder: .\setup.ps1

# If PowerShell blocks scripts:
# Set-ExecutionPolicy -Scope CurrentUser RemoteSigned

pip install --upgrade pip
pip install -r requirements.txt

# Environment file
copy .env.example .env
# Edit .env — database, SECRET_KEY, CORS, etc.
```

### Important `.env` values (development)

```env
APP_ENV=development
DEBUG=true
SECRET_KEY=dev-only-change-me-to-long-random-string

# Database — see section 3
DB_HOST=localhost\SQLEXPRESS
DB_NAME=mymadec
DB_USER=
DB_PASSWORD=
DB_DRIVER=ODBC Driver 18 for SQL Server

# Frontend URL (Vite default port)
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000

# Skip real email in dev
DISABLE_EMAIL=true

# Load demo users, products, orders on startup
SEED_DEMO=true
```

---

## 5. Database migrations (Alembic)

**Always run Alembic from the `backend/` folder with the virtual environment activated.**

### Apply all migrations (first time & after pull)

```powershell
cd backend
.\venv\Scripts\Activate.ps1
alembic upgrade head
```

This applies scripts in `backend/alembic/versions/` (e.g. initial schema).

### Check current revision

```powershell
alembic current
```

### Create a new migration (after changing SQLAlchemy models)

```powershell
alembic revision --autogenerate -m "describe your change"
# Review the generated file in alembic/versions/ before committing
alembic upgrade head
```

### Roll back one step (use with care)

```powershell
alembic downgrade -1
```

### How migrations relate to app startup

| Mode | Behaviour |
|------|-----------|
| `DEBUG=true` | On API startup, tables may also be created via `create_all` **in addition** to migrations — still run `alembic upgrade head` for a clean, team-aligned schema |
| Production | **Only** Alembic migrations — no `create_all` |

**Rule for contributors:** if you change models under `app/models/`, add an Alembic revision and document it in your PR.

---

## 6. Run the backend API

```powershell
cd backend
.\venv\Scripts\Activate.ps1

# Option 1
python run_server.py

# Option 2
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

| URL | Description |
|-----|-------------|
| http://localhost:8000/health | Health check |
| http://localhost:8000/docs | Swagger UI (**only when `DEBUG=true`**) |

On first successful startup, the API **seeds** data (see logs):

- Default **admin** user (if missing)  
- ETL **service token** (printed once — save it or set `ETL_SERVICE_TOKEN` in `.env`)  
- Empty banner slots  
- **Demo data** if `SEED_DEMO=true` or `DEBUG=true`

Watch the console for lines like:

```
DEFAULT ADMIN CREATED
  Email   : admin@mymadec.com
  Password: Test1234!
```

---

## 7. Frontend setup

```powershell
cd frontend

npm install

copy .env.example .env
```

`frontend/.env`:

```env
VITE_API_URL=http://localhost:8000/api/v1
```

```powershell
npm run dev
```

Open **http://localhost:5173** and log in with a seeded account (see below).

### Production build (optional check)

```powershell
npm run build
npm run preview
```

---

## 8. Demo accounts (local development)

When `SEED_DEMO=true` or `DEBUG=true`, all demo accounts use password:

**`Test1234!`**

| Email | Role |
|-------|------|
| admin@mymadec.com | admin |
| gestionnaire@mymadec.test | gestionnaire |
| acheteur1@mymadec.test | acheteur |
| acheteur2@mymadec.test | acheteur |
| acheteur3@mymadec.test | acheteur |
| service@mymadec.test | service |

---

## 9. Run everything with Docker (backend + DB)

From `backend/`:

```powershell
copy .env.example .env
# Edit DB_PASSWORD and other vars
docker compose up --build
```

- API: http://localhost:8000  
- SQL Server: `localhost:1433`  

You still need to **create `mymadec` database** and run **migrations** inside the API container or from host:

```powershell
docker compose exec api alembic upgrade head
```

---

## 10. Running tests (backend)

Tests use **SQLite** in memory — **no SQL Server required**.

```powershell
cd backend
.\venv\Scripts\Activate.ps1
pytest tests/ -v
```

---

## 11. User roles (for testing)

| Role | Access |
|------|--------|
| `admin` | Full access, banners, sync, users |
| `gestionnaire` | Orders, users (limited) |
| `acheteur` | Catalogue, own orders, cart |
| `service` | ETL endpoints (Bearer service token) |

---

## 12. Project layout (quick map)

```
backend/
├── app/
│   ├── api/v1/       # HTTP routes
│   ├── core/         # config, security, auth
│   ├── db/           # session, init_db, seed_demo
│   ├── models/       # SQLAlchemy models
│   ├── schemas/      # Pydantic DTOs
│   └── services/     # business logic
├── alembic/          # migrations
├── tests/
├── uploads/          # images (created at runtime, gitignored)
├── .env.example
└── requirements.txt

frontend/
├── src/
│   ├── components/
│   ├── pages/
│   ├── lib/api.ts    # Axios client
│   └── store/        # Zustand (auth, cart)
└── .env.example
```

---

## 13. Optional: Firebase (push notifications)

1. Create a Firebase project → Service account → download JSON key.  
2. Save as `backend/firebase-credentials.json` (gitignored).  
3. In `.env`:

   ```env
   FIREBASE_CREDENTIALS_PATH=firebase-credentials.json
   ```

If the file is missing, push features are skipped; the rest of the API works.

---

## 14. Optional: SMTP (password reset emails)

For real reset emails, configure:

```env
SMTP_HOST=...
SMTP_PORT=587
SMTP_USER=...
SMTP_PASSWORD=...
SMTP_FROM_NAME=My Madec
DISABLE_EMAIL=false
```

For local dev, keep `DISABLE_EMAIL=true`.

---

## 15. Troubleshooting

### `Can't open lib 'ODBC Driver 18 for SQL Server'`

- Install [ODBC Driver 18](https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server).  
- Or set `DB_DRIVER=ODBC Driver 17 for SQL Server` if only 17 is installed.

### `Login failed for user 'sa'` / connection refused

- Check `DB_HOST` (`localhost\SQLEXPRESS` vs `localhost` + port).  
- Verify SQL Server service is running (**services.msc** → SQL Server (SQLEXPRESS)).  
- Confirm mixed-mode auth if using `sa`.  
- Try SSMS with the same host/user/password first.

### `Database 'mymadec' does not exist`

Run `CREATE DATABASE mymadec;` in SSMS or `sqlcmd`.

### Alembic / migration errors after pulling

```powershell
alembic upgrade head
```

If your local DB is broken beyond repair (dev only):

```sql
DROP DATABASE mymadec;
CREATE DATABASE mymadec;
```

Then `alembic upgrade head` again.

### CORS errors in the browser

Ensure `ALLOWED_ORIGINS` in `backend/.env` includes `http://localhost:5173`.

### Frontend cannot reach API

- Backend running on port **8000**  
- `VITE_API_URL=http://localhost:8000/api/v1` in `frontend/.env`  
- Restart `npm run dev` after changing `.env`

### `pip install pyodbc` fails

- Use Python 3.11/3.12 (`py -3.12 -m venv .venv`). Python 3.14 cannot install the pinned stack.  
- On Windows, Microsoft C++ build tools are usually **not** needed if pip picks a binary wheel.

---

## 16. Contribution checklist

Before opening a PR:

- [ ] `alembic upgrade head` runs cleanly on a fresh DB  
- [ ] New model changes include an Alembic revision  
- [ ] `pytest tests/ -v` passes  
- [ ] `npm run build` passes (if you touched frontend)  
- [ ] No secrets in git (`.env`, `firebase-credentials.json`, passwords)  
- [ ] README / this doc updated if setup steps changed  

---

## 17. Quick reference (copy-paste)

```powershell
# Terminal 1 — Backend
cd backend
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
# → edit .env, create DB in SSMS
alembic upgrade head
python run_server.py

# Terminal 2 — Frontend
cd frontend
npm install
copy .env.example .env
npm run dev
```

| Service | URL |
|---------|-----|
| Frontend | http://localhost:5173 |
| API | http://localhost:8000 |
| API docs | http://localhost:8000/docs |

---

**Questions?** Contact the project maintainer or open an issue on GitHub.
