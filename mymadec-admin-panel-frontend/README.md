# My Madec — frontend admin **v2** (thème Minia)

Version 2 du frontend d'administration My Madec.
**Mêmes données, mêmes APIs, même logique que la v1** (`my-madec-frontend-test`) —
seule l'interface change : elle adopte le design system **Minia** (Themesbrand),
fourni comme référence dans `../my-madec-frontend-test-v2-UI/Admin`.

**La v2 est désormais l'application principale, servie à la racine `/`**
(`/login`, `/dashboard`, …). Voir `vite.config.ts` (`base: "/"`),
le `basename` du router dans `src/App.tsx`, et [nginx/mymadec.conf](nginx/mymadec.conf)
qui sert le build v2 à la racine (v2 → `/var/www/html`).

- Migration visuelle détaillée : [docs/UI-V2-MINIA.md](docs/UI-V2-MINIA.md)
- Architecture + diagrammes (Mermaid) : [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- Couverture API : [API_COVERAGE.md](API_COVERAGE.md)

## Stack

React 19 · TypeScript · Vite · Tailwind CSS · TanStack React Query · Zustand ·
React Hook Form + Zod · Axios (refresh JWT automatique) · react-hot-toast.

## Démarrer

```bash
npm install
npm run dev          # http://localhost:5173/ (proxy API via VITE_DEV_PROXY_TARGET)
npm run build        # tsc -b && vite build → dist/ (assets préfixés /)
npm run lint
```

Variables d'environnement utiles :

| Variable | Défaut | Rôle |
|---|---|---|
| `VITE_API_URL` | `/api/v1` | base des appels REST |
| `VITE_MEDIA_BASE_URL` | origine de l'API | origine servant `/uploads` |
| `VITE_DEV_PROXY_TARGET` | — | cible du proxy dev |

## Structure

```
src/
├── pages/            # écrans (lazy loaded)
├── components/
│   ├── layout/       # AppLayout, Sidebar (Minia claire), TopBar, AuthShell
│   ├── ui/           # Modal, Pagination, badges, états vides…
│   └── products|staff|promptinos/
├── lib/              # api.ts, api/services.ts, types, rôles, nav
├── store/            # Zustand: auth (persist), cart
├── hooks/            # useCatalog, usePromptinos, useUnreadCount…
└── index.css         # design tokens Minia + classes composants
```

## Thème

Toute l'identité visuelle passe par les tokens de `src/index.css` (`--madec-*`) et
`tailwind.config.js` (`madec.*`, `primary.*`). Pour modifier le thème, ne toucher
que ces deux fichiers — voir [docs/UI-V2-MINIA.md](docs/UI-V2-MINIA.md).
