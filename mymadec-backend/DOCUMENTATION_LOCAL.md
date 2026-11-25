# My Madec Backend — Documentation serveur local (sans Docker)

Documentation du backend **my-madec-backend-test** pour un serveur / PC Windows **sans Docker**.

Guide global stack (front + back + ETL) : `docs/SETUP_SERVEUR_LOCAL.md` à la racine du workspace Mymadic.

---

## 0. À installer sur le serveur (ce projet)

| # | Logiciel | Pourquoi |
|---|----------|----------|
| 1 | **Git** | Cloner / pull le repo |
| 2 | **Python 3.10+** (idéalement 3.11/3.12) | Runtime API — cocher *Add to PATH* |
| 3 | **Microsoft SQL Server** (Express OK) | Base `mymadec` (ou accès distant + tunnel) |
| 4 | **ODBC Driver 18 for SQL Server** | Connexion `pyodbc` |
| 5 | **SSMS** (recommandé) | Créer la DB, inspecter les tables |

Vérif PowerShell :

```powershell
git --version
py -3 --version
Get-OdbcDriver | Where-Object { $_.Name -like "*SQL Server*" }
```

**Pas besoin de :** Docker, Redis, Node.js (Node = frontend uniquement).

Liens utiles :
- Python : https://www.python.org/downloads/windows/
- SQL Express : https://www.microsoft.com/sql-server/sql-server-downloads
- ODBC 18 : https://learn.microsoft.com/sql/connect/odbc/download-odbc-driver-for-sql-server
- SSMS : https://learn.microsoft.com/sql/ssms/download-sql-server-management-studio-ssms

---

## 1. Rôle du backend

API REST **FastAPI** qui :

- authentifie les utilisateurs (admin, gestionnaire, acheteur) ;
- expose le catalogue produits (catégories, sous-catégories, types, produits) ;
- gère les commandes B2B et le plafond acheteur ;
- synchronise les données avec le système ERP / Sabile (ETL) ;
- sert les fichiers uploadés (`/uploads/...`) ;
- alimente l’admin web et l’app mobile.

**Principe prix :** les prix viennent de **Sabile** tels quels. Aucun taux / frais espèces n’est ajouté sur le total commande (`fixedtax = 0`, `dueamount = amount`).

---

## 2. Stack technique

| Élément | Technologie |
|--------|-------------|
| Langage | Python 3.10+ |
| Framework | FastAPI + Uvicorn |
| ORM | SQLAlchemy |
| Migrations | Alembic |
| Base de données | Microsoft SQL Server |
| Driver | ODBC Driver 17 ou 18 + `pyodbc` |
| Auth | JWT (access + refresh) |

Structure principale :

```
my-madec-backend-test/
├── app/
│   ├── main.py              # point d’entrée FastAPI
│   ├── api/v1/              # routes HTTP
│   ├── core/                # config, sécurité, deps
│   ├── models/              # tables SQLAlchemy
│   ├── schemas/             # Pydantic (request/response)
│   ├── services/            # logique métier
│   └── db/                  # session, bootstrap, seed
├── alembic/versions/        # migrations
├── tests/
├── uploads/                 # images / fichiers
├── .env                     # config locale (ne pas committer)
├── requirements.txt
└── alembic.ini
```

---

## 3. Prérequis (sans Docker)

1. **Python 3.10+** (`py -3 --version`)
2. **Microsoft SQL Server** (Express / Standard) **installé localement**, **ou** accès distant via tunnel SSH
3. **ODBC Driver 18 for SQL Server**
4. (Optionnel) **SSMS** pour créer / inspecter la base
5. **Git**

Pas besoin de Docker, Redis, ni Nginx pour le développement local.

---

## 4. Installation

```powershell
cd d:\Mymadic\my-madec-backend-test
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
py -3 -m pip install -r requirements.txt
copy .env.example .env
```

Édite `.env` selon ton cas (ci-dessous).

---

## 5. Configuration `.env` (local, sans Docker)

### Cas A — SQL Server sur la même machine

```env
APP_ENV=development
DEBUG=true
ENABLE_DOCS=true
SECRET_KEY=change-me-local-dev-secret

DB_HOST=localhost
DB_PORT=1433
DB_NAME=mymadec
DB_USER=sa
DB_PASSWORD=TonMotDePasse
DB_DRIVER=ODBC Driver 18 for SQL Server

ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
FRONTEND_BASE_URL=http://localhost:5173

UPLOAD_DIR=uploads
DISABLE_EMAIL=true
SEED_DEMO=true
FIXEDTAX_RATE=0.0
```

Instance Express nommée :

```env
DB_HOST=localhost\SQLEXPRESS
```

(laisse `DB_PORT` vide / non utilisé selon le code de connexion nommé).

Créer la base une fois :

```sql
CREATE DATABASE mymadec;
```

### Cas B — SQL Server distant (VPS) via tunnel SSH

Sur le PC local, ouvrir un tunnel (garder le terminal ouvert) :

```powershell
ssh -L 11433:localhost:1433 root@TON_SERVEUR_IP
```

Puis dans `.env` :

```env
DB_HOST=127.0.0.1
DB_PORT=11433
DB_NAME=mymadec
DB_USER=sa
DB_PASSWORD=...
```

---

## 6. Migrations

Toujours avant de démarrer (ou après un `git pull`) :

```powershell
cd d:\Mymadic\my-madec-backend-test
py -3 -m alembic upgrade head
```

Migrations importantes récentes :

- `010_catalog_sort_and_types` — table `catalog_types` + `products.sort_order`

---

## 7. Démarrer l’API (sans Docker)

```powershell
cd d:\Mymadic\my-madec-backend-test
py -3 -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

| URL | Usage |
|-----|--------|
| http://127.0.0.1:8000 | API |
| http://127.0.0.1:8000/docs | Swagger (si `ENABLE_DOCS=true`) |
| http://127.0.0.1:8000/api/v1/... | Endpoints métier |

Si **WinError 10013** : le port 8000 est déjà pris. Arrêter l’ancien process Python / uvicorn, puis relancer.

Si **SQL Server n'existe pas / accès refusé** : SQL arrêté, mauvais `DB_*`, ou tunnel SSH fermé.

---

## 8. Comment ça marche (flux)

```
Client (Admin / Mobile)
        │
        ▼
   FastAPI (/api/v1)
        │
        ├── Auth JWT
        ├── Services métier
        └── SQLAlchemy
                │
                ▼
         SQL Server (mymadec)
```

Au démarrage (`app/main.py`) :

1. charge la config `.env` ;
2. attend que la DB soit joignable ;
3. applique les migrations Alembic si besoin ;
4. seed admin / données démo selon `SEED_DEMO`.

### Modules API (`/api/v1`)

| Router | Rôle |
|--------|------|
| `auth` | login, refresh, reset password |
| `users` | CRUD utilisateurs, rôles, plafond |
| `products` | catalogue produits, filtres, mobile |
| `catalog` | catégories / sous-catégories / types + **reorder** |
| `orders` | création / suivi commandes |
| `payment_methods` | mode de paiement utilisateur |
| `settings` | réglages (cash-fee désactivé → toujours 0) |
| `sync` | endpoints ETL / Sabile |
| `dashboard` | stats admin + `mobile_catalog` |
| `banners` / `notifications` / `annuaire` | contenu & org |

### Catalogue & tri

- Tables : `catalog_categories`, `catalog_sous_categories`, `catalog_types`, `products`
- Champ `sort_order` (10, 20, 30…) sur chaque niveau
- Endpoints reorder :
  - `PUT /catalog/reorder/categories`
  - `PUT /catalog/reorder/sous-categories`
  - `PUT /catalog/reorder/types`
  - `PUT /catalog/reorder/products`
- L’arbre mobile : `GET /catalog/categories/tree` (déjà trié)
- Produits mobile : `GET /products/mobile` (ordre `sort_order`, puis nom)

### Commandes & prix

1. Lignes valorisées avec le prix produit en base (issu de Sabile / sync)
2. Total = somme des lignes
3. **Pas de surcharge** espèces
4. `amount` = `dueamount`, `fixedtax` = `0`

---

## 9. Auth (résumé)

1. `POST /api/v1/auth/login` → access + refresh token
2. Appels suivants : header `Authorization: Bearer <access_token>`
3. Rôles : `admin`, `gestionnaire`, `acheteur` (+ service ETL)

---

## 10. Fichiers / médias

- Dossier local : `UPLOAD_DIR=uploads`
- Servis sous `http://127.0.0.1:8000/uploads/...`
- En local, le frontend Vite proxyifie `/uploads` vers le backend

---

## 11. Déploiement serveur local (prod légère, toujours sans Docker)

Exemple Windows / IIS reverse proxy **ou** Nginx Windows / Linux :

1. Installer Python + ODBC + SQL Server
2. Cloner le repo, venv, `pip install -r requirements.txt`
3. Configurer `.env` (`APP_ENV=production`, `DEBUG=false`, `ENABLE_DOCS=false`, `SECRET_KEY` fort)
4. `alembic upgrade head`
5. Lancer avec un process manager (NSSM / Task Scheduler / systemd) :

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2
```

6. Reverse-proxy HTTPS vers `:8000` (`/api` + `/uploads`)

---

## 12. Checklist dépannage

| Symptôme | Action |
|----------|--------|
| Port 8000 refusé | Tuer l’ancien uvicorn |
| DB timeout | Vérifier SQL / tunnel SSH `11433` |
| Migration échoue | Vérifier droits SQL + `alembic current` |
| CORS front | Ajouter l’origine dans `ALLOWED_ORIGINS` |
| Images 404 | Vérifier `UPLOAD_DIR` et proxy `/uploads` |

---

## 13. Commandes utiles

```powershell
# Statut migrations
py -3 -m alembic current

# Appliquer migrations
py -3 -m alembic upgrade head

# Lancer API
py -3 -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# Tests (SQLite mémoire / fichier via conftest)
py -3 -m pytest -q
```
