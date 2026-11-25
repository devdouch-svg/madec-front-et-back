# My Madec — API coverage (web app)

## Web UI (JWT) — implemented

| Module | Endpoints | UI |
|--------|-----------|-----|
| **Auth** | login, logout, refresh*, reset request/confirm, change-password | Login, forgot/reset, profile |
| **Users** | me, update me, plafond, list, CRUD, toggle, reset-pw, plafond, role, payment-mode, orders | Users, profile, payment (admin) |
| **Products** | list, search, filters, get, by-code, CRUD, toggle, assign, image | Products |
| **Orders** | list, me, create, get, lines, history, bl, cancel, status, validate | Orders |
| **Annuaire** | list, get | Annuaire |
| **Banners** | list, update, toggle, image | Banners (admin) |
| **Notifications** | list, unread, read, read-all, send, delete | Notifications, top bar |
| **Payment** | mine, all, patch me, admin toggle | Payment methods |
| **Dashboard** | aggregate | Dashboard |
| **Sync (admin)** | overview, logs, rotate token | Sync ETL |

\*Refresh is used automatically by the Axios interceptor.

## ETL only (service Bearer token) — not in web UI

These are for the external ETL integration, documented on **Sync ETL**:

- `GET /sync/health`
- `POST /sync/products`, `/sync/products/bulk`
- `POST /sync/users`, `/sync/users/bulk`
- `PATCH /sync/users/{id}/deactivate`
- `POST /sync/orders/push`
- `PATCH /sync/orders/{id}/status|bl|flag`

## Code reference

Typed client: `frontend/src/lib/api/services.ts`
