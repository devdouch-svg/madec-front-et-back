# My Madec Frontend Admin (v2) — Documentation serveur local (sans Docker)

Documentation du frontend **my-madec-frontend-test-v2** pour un serveur / PC Windows **sans Docker**.

Guide global stack (front + back + ETL) : `docs/SETUP_SERVEUR_LOCAL.md` à la racine du workspace Mymadic.

---

## 0. À installer sur le serveur (ce projet)

| # | Logiciel | Pourquoi |
|---|----------|----------|
| 1 | **Git** | Cloner / pull le repo |
| 2 | **Node.js 20 LTS+** | `npm` + Vite / React |
| 3 | Backend My Madec joignable | API sur `127.0.0.1:8000` (ou proxy distant) |

Vérif PowerShell :

```powershell
git --version
node -v
npm -v
```

**Optionnel (prod locale) :** Nginx ou IIS pour servir le dossier `dist/` après `npm run build`.

**Pas besoin de :** Docker, Python, SQL Server, ODBC (ça c’est backend / ETL).

Liens utiles :
- Node.js 20 LTS : https://nodejs.org/
- Git : https://git-scm.com/download/win

---

## 1. Rôle du frontend

Interface **admin / gestionnaire / acheteur** (back-office web) qui :

- se connecte à l’API backend My Madec ;
- gère utilisateurs, produits, commandes, catalogue ;
- permet de **trier le catalogue** (catégories → sous-catégories → types → produits) ;
- affiche dashboard, bannières, notifications, sync ETL.

Ce n’est **pas** l’app mobile Flutter. Le mobile consomme la même API.

---

## 2. Stack technique

| Élément | Technologie |
|--------|-------------|
| Langage | TypeScript |
| UI | React 19 |
| Build / dev server | Vite |
| Data fetching | TanStack React Query |
| Routing | React Router |
| State auth | Zustand |
| Styles | Tailwind CSS |
| HTTP | Axios |

Structure principale :

```
my-madec-frontend-test-v2/
├── src/
│   ├── App.tsx                 # routes
│   ├── pages/                  # écrans
│   ├── components/             # UI / layout / auth
│   ├── hooks/                  # React Query hooks
│   ├── lib/
│   │   ├── api.ts              # client Axios
│   │   ├── api/services.ts     # appels API métier
│   │   ├── config.ts           # VITE_* URLs
│   │   ├── nav.ts              # menu latéral
│   │   ├── types.ts
│   │   └── staffCapabilities.ts
│   └── store/auth.ts           # session JWT
├── .env / .env.example
├── vite.config.ts              # proxy /api + /uploads
├── package.json
└── dist/                       # build production (après npm run build)
```

---

## 3. Prérequis (sans Docker)

1. **Node.js 20 LTS+** (`node -v`, `npm -v`)
2. Backend My Madec joignable (local `127.0.0.1:8000` **ou** API distante)
3. Navigateur moderne (Chrome / Edge)

Pas besoin de Docker ni Nginx pour le développement.

---

## 4. Installation

```powershell
cd d:\Mymadic\my-madec-frontend-test-v2
npm install
copy .env.example .env
```

---

## 5. Configuration `.env` (local)

### Mode recommandé — backend local

```env
VITE_API_URL=/api/v1
VITE_DEV_PROXY_TARGET=http://127.0.0.1:8000
```

Vite proxyfie :

- `/api/*` → `http://127.0.0.1:8000/api/*`
- `/uploads/*` → `http://127.0.0.1:8000/uploads/*`

→ pas de CORS en dev.

### Mode — API distante (VPS) sans backend local

```env
VITE_API_URL=/api/v1
VITE_DEV_PROXY_TARGET=http://194.164.72.226:8034
```

### Option médias

```env
# VITE_MEDIA_BASE_URL=http://127.0.0.1:8000
```

---

## 6. Démarrer en local (sans Docker)

Terminal 1 — backend (voir doc backend) :

```powershell
cd d:\Mymadic\my-madec-backend-test
py -3 -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Terminal 2 — frontend :

```powershell
cd d:\Mymadic\my-madec-frontend-test-v2
npm run dev
```

Ouvrir : **http://localhost:5173**

Login admin (selon seed / `.env` backend).

---

## 7. Comment ça marche

```
Navigateur (localhost:5173)
        │
        │  /api/v1/...  (proxy Vite)
        ▼
Backend FastAPI (127.0.0.1:8000)
        │
        ▼
SQL Server
```

1. **Login** → tokens stockés (Zustand / localStorage)
2. Chaque page appelle l’API via `src/lib/api` + `services.ts`
3. React Query cache les listes (produits, commandes, catalogue…)
4. Les droits d’écran viennent de `nav.ts` + `staffCapabilities.ts` + `RequireRole`

### Pages principales

| Route | Page | Qui |
|-------|------|-----|
| `/login` | Connexion | public |
| `/dashboard` | Tableau de bord | connecté |
| `/products` | Produits / catalogue | connecté |
| `/orders` | Commandes | connecté |
| `/users` | Utilisateurs | admin, gestionnaire |
| `/catalog` | Référentiels catalogue | admin, gestionnaire |
| `/catalog/order` | **Ordre catalogue** (drag & drop) | admin, gestionnaire |
| `/payment-methods` | Modes de paiement | acheteur, admin |
| `/banners` | Bannières | admin |
| `/sync` | Sync ETL | admin |
| `/annuaire` | Annuaire org | admin |
| `/notifications` | Notifications | connecté |
| `/profile` | Profil | connecté |

### Ordre catalogue (`/catalog/order`)

Page à **4 colonnes** :

1. Catégories  
2. Sous-catégories (après sélection catégorie)  
3. Types (après sélection sous-catégorie)  
4. Produits (filtrés par sélection)

- Drag & drop + flèches  
- Enregistre via `PUT /catalog/reorder/...`  
- L’ordre est ensuite lu par le **mobile** (`sort_order`)

### Paiement

La page **Mode de paiement** gère uniquement l’attribution `especes` / `carte` / `les_deux`.  
**Plus de section « Taux ajouté sur l'achat »** : les prix restent ceux de Sabile.

---

## 8. Build production (serveur local sans Docker)

```powershell
cd d:\Mymadic\my-madec-frontend-test-v2
npm run build
```

Sortie : dossier `dist/`.

### Servir les fichiers statiques

Exemples :

**Option A — Vite preview (test rapide)**

```powershell
npm run preview
```

**Option B — Nginx / IIS / Apache**

1. Copier le contenu de `dist/` vers le dossier web du serveur
2. Configurer le reverse-proxy :

```nginx
server {
  listen 80;
  server_name ton-serveur.local;
  root /var/www/mymadec-admin;
  index index.html;

  location / {
    try_files $uri $uri/ /index.html;
  }

  location /api/ {
    proxy_pass http://127.0.0.1:8000/api/;
  }

  location /uploads/ {
    proxy_pass http://127.0.0.1:8000/uploads/;
  }
}
```

En production, le front parle en relatif (`/api/v1`) : le reverse-proxy envoie vers le backend local, **toujours sans Docker**.

---

## 9. Variables d’environnement (résumé)

| Variable | Rôle |
|----------|------|
| `VITE_API_URL` | Préfixe API (souvent `/api/v1`) |
| `VITE_DEV_PROXY_TARGET` | Cible du proxy Vite en dev |
| `VITE_MEDIA_BASE_URL` | Base URL images (optionnel) |

Ces variables sont lues au **build** (`VITE_*`). Après changement, relancer `npm run dev` ou rebuild.

---

## 10. Checklist dépannage

| Symptôme | Action |
|----------|--------|
| Page blanche / erreur API | Backend allumé ? `VITE_DEV_PROXY_TARGET` correct ? |
| 401 permanent | Relogin ; token expiré |
| Images cassées | Proxy `/uploads` + fichiers dans `backend/uploads` |
| Menu manquant | Rôle utilisateur (admin / gestionnaire / acheteur) |
| Tri catalogue ne change rien | Migration `010` appliquée côté backend ? Hot reload mobile / hard refresh admin |

---

## 11. Commandes utiles

```powershell
npm install          # dépendances
npm run dev          # http://localhost:5173
npm run build        # génère dist/
npm run preview      # teste le build
npm run lint         # ESLint
```

---

## 12. Lien avec le backend

Voir aussi : `my-madec-backend-test/DOCUMENTATION_LOCAL.md`

Ordre de démarrage typique sur un serveur local **sans Docker** :

1. SQL Server accessible  
2. Backend uvicorn `:8000`  
3. Frontend `npm run dev` **ou** `dist/` derrière Nginx/IIS  
4. (Mobile) pointe vers la même API
