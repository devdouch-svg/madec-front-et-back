# Architecture — frontend admin v2

Frontend React 19 + TypeScript + Vite + Tailwind. Même backend et mêmes APIs que la v1 ;
seul le thème (Minia) diffère — voir [UI-V2-MINIA.md](UI-V2-MINIA.md).

## Vue d'ensemble

```mermaid
flowchart LR
    subgraph Browser["Navigateur (admin / gestionnaire / acheteur)"]
        UI["React 19 + Vite\nThème Minia (Tailwind)"]
        RQ["TanStack React Query\n(cache serveur)"]
        ZS["Zustand\nauth + cart (persist)"]
        AX["Axios\nintercepteurs JWT"]
        UI --> RQ --> AX
        UI --> ZS
        ZS --> AX
    end

    subgraph Serveur
        NG["nginx\n(statique + /api + /uploads)"]
        BE["Backend REST\n/api/v1"]
        DB[("Base de données")]
        ETL["Serveur intermédiaire\n(Sync ETL)"]
    end

    AX -->|"Bearer access token"| NG --> BE --> DB
    ETL -->|"import périodique"| BE
```

## Couches du frontend

```mermaid
flowchart TD
    subgraph Pages["src/pages (lazy loaded)"]
        P1[DashboardPage]
        P2[ProductsPage]
        P3[OrdersPage]
        P4[UsersPage]
        P5[CatalogPage]
        P6["Promptinos / Banners / Annuaire / Sync / Notifications / Paiement / Profil"]
        P7["Login / ForgotPassword / ResetPassword"]
    end

    subgraph Layout["src/components/layout"]
        L1["AppLayout\n(garde d'auth + hydratation)"]
        L2["Sidebar (Minia claire)"]
        L3["TopBar (70px)"]
        L4["AuthShell (pages publiques)"]
    end

    subgraph UIKit["src/components/ui + index.css"]
        U1[".card / .btn / .input"]
        U2[".data-table / .status-badge"]
        U3["Modal / ConfirmModal / Pagination / EmptyState"]
    end

    subgraph Data["src/lib + src/store + src/hooks"]
        D1["api.ts (axios + refresh 401)"]
        D2["api/services.ts (endpoints typés)"]
        D3["store/auth.ts · store/cart.ts"]
        D4["hooks: useCatalog, usePromptinos, useUnreadCount…"]
    end

    P7 --> L4
    P1 & P2 & P3 & P4 & P5 & P6 --> L1
    L1 --> L2 & L3
    Pages --> UIKit
    Pages --> D4 --> D2 --> D1
    L1 --> D3
```

## Flux d'authentification

```mermaid
sequenceDiagram
    participant U as Utilisateur
    participant L as LoginPage
    participant A as store/auth (Zustand)
    participant X as axios (api.ts)
    participant B as Backend /api/v1

    U->>L: email + mot de passe
    L->>B: POST /auth/login
    B-->>L: access + refresh tokens
    L->>A: setSession(tokens, user)
    A->>A: persist (localStorage)

    Note over X,B: requêtes suivantes
    X->>B: GET ... (Authorization: Bearer access)
    B-->>X: 401 (token expiré)
    X->>B: POST /auth/refresh (refresh token)
    B-->>X: nouveau access token
    X->>B: rejoue la requête initiale
    alt refresh échoue
        X->>A: clearSession()
        X->>U: redirection /login
    end
```

## Navigation par rôle

```mermaid
flowchart TD
    R{{"Rôle (JWT)"}}
    R -->|acheteur| A["Tableau de bord · Produits · Promptinos\nCommandes (panier) · Notifications · Paiement"]
    R -->|gestionnaire| G["+ Utilisateurs · Référentiels\n(section Gestion, périmètre agence)"]
    R -->|admin| AD["+ Annuaire · Bannières · Sync ETL\n(section Administration)"]
    R -->|service| S["Aucun accès UI\n(token machine ETL uniquement)"]
```

- La liste est déclarée dans [src/lib/nav.ts](../src/lib/nav.ts) (`navSectionsForRole`).
- Les routes sont protégées par `AppLayout` (session) et `RequireRole` (rôle).

## Cycle de vie d'une commande (UI)

```mermaid
stateDiagram-v2
    [*] --> pending : création (acheteur)
    pending --> validated : validation
    validated --> processing : préparation
    processing --> ready : prête
    ready --> delivered : livraison
    pending --> cancelled : annulation
    validated --> cancelled
    delivered --> [*]
    cancelled --> [*]
```

Chaque état a sa classe `.status-badge--*` (palette soft Minia) dans
[src/index.css](../src/index.css).
