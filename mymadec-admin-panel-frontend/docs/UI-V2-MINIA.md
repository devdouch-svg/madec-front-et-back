# UI v2 — Thème Minia

La v2 du frontend admin reprend **exactement les mêmes données, APIs et logique métier** que la v1.
Seule la couche visuelle a changé : elle adopte le design system du template **Minia**
(Themesbrand, Bootstrap 5) fourni dans `../my-madec-frontend-test-v2-UI/Admin`.

## Principe de la migration

Le code des pages n'a (presque) pas bougé : toute l'identité visuelle passe par des
**design tokens** centralisés. La migration a consisté à remapper les valeurs des tokens,
pas à réécrire les écrans.

| Couche | Fichier | Rôle |
|---|---|---|
| Tokens Tailwind | [tailwind.config.js](../tailwind.config.js) | palette `madec.*` et échelle `primary.*` |
| Tokens CSS + composants | [src/index.css](../src/index.css) | variables `--madec-*` + classes `.btn`, `.card`, `.data-table`, `.status-badge`, `.sidebar-link`… |
| Layout | `src/components/layout/` | Sidebar claire, topbar 70 px, AuthShell |
| Police | [index.html](../index.html) | IBM Plex Sans (Google Fonts) |

## Mapping des couleurs (v1 → v2 Minia)

| Token | v1 (MADEC bleu) | v2 (Minia) | Source Minia |
|---|---|---|---|
| `--madec-primary` | `#00578F` | `#5156be` | `$blue` |
| `--madec-success` | `#06A017` | `#2ab57d` | `$green` |
| `--madec-danger` | `#EB001B` | `#fd625e` | `$red` |
| `--madec-warning` | — | `#ffbf53` | `$yellow` |
| `--madec-info` | — | `#4ba6ef` | `$cyan` |
| `--madec-text` | `#252525` | `#313533` | `$gray-700` (body color) |
| `--madec-text-secondary` | `#7C7C7C` | `#545a6d` | sidebar item |
| `--madec-text-muted` | `#979797` | `#74788d` | `$gray-600` |
| `--madec-border` | `#E2E8F0` | `#e9e9ef` | `$gray-200` |
| `--madec-sidebar-bg` | bleu foncé (`primary-950`) | `#fbfaff` | `--bs-sidebar-bg` |
| Fond du body | `#F8F8F8` | `#ffffff` | `$body-bg: $white` |

## Signature visuelle Minia reprise

- **Police** : IBM Plex Sans (400/500/600/700), remplace Inter.
- **Sidebar claire** : `#fbfaff`, 250 px, bordure droite `#e9e9ef` ; items `#545a6d`,
  hover/actif indigo `#5156be` (l'actif garde un fond `--madec-primary-tint`).
- **Topbar** : blanche, 70 px, bordure basse ; boutons d'icônes sans bordure,
  arrondis pleins, hover gris `#f8f9fa` ; avatar rond.
- **Cartes** : fond blanc, bordure `#e9e9ef`, ombre Minia
  `rgba(116,120,141,.10) 0 5px 20px -6px`, rayon `0.25rem`.
- **Badges "soft"** : fond teinté + texte de la couleur (ex. `#d4f0e5` / `#2ab57d`),
  rayon `0.25rem` (plus de pills).
- **Boutons** : rayon `0.25rem`, graisse 500 ; le bouton secondaire devient
  "outline" (fond plein au survol), comportement Bootstrap.

## Dashboard (widgets Minia + ApexCharts)

Le tableau de bord reprend les widgets du dashboard Minia (`views/index.ejs` +
`assets/js/pages/dashboard.init.js`), rendus avec **react-apexcharts** :

| Widget Minia | Équivalent v2 | Composant |
|---|---|---|
| Cartes "My Wallet" (valeur + sparkline + badge soft) | CA, commandes du mois, en attente, actifs (staff) / dépensé, commandes, notifications (acheteur) | `StatWidgetCard` + `MiniSparkline` |
| "Wallet Balance" (pie + légende) | Commandes par statut (légende cliquable → `/orders?status=…`) | `OrdersPieCard` + `StatusPie` |
| "Invested Overview" (radialBar gradient) | Jauge du plafond mensuel (acheteur) | `PlafondGaugeCard` + `RadialGauge` |

Fichiers : `src/components/dashboard/charts.tsx` (composants),
`src/components/dashboard/chartData.ts` (palette par statut + agrégation).
**Aucune nouvelle API** : les sparklines sont dérivées côté client de
`recent_orders` (14 jours glissants) et la répartition de `orders_by_status`,
déjà présents dans la réponse `/dashboard`.

## Ce qui n'a PAS changé

- Tous les appels API (`src/lib/api.ts`, `src/lib/api/services.ts`), le refresh token,
  les stores Zustand (`auth`, `cart`), React Query, le routing et les gardes de rôles.
- Les noms de classes utilitaires (`.btn-primary`, `.card`, `.status-badge--*`…) :
  les pages compilent sans modification.
- Les types (`src/lib/types.ts`) et la config (`src/lib/config.ts`).

## Ajuster le thème

1. **Couleur de marque** : changer `--madec-primary` dans `src/index.css` **et**
   `madec.primary` + l'échelle `primary` dans `tailwind.config.js`.
2. **Sidebar sombre (variante Minia)** : dans `src/index.css`, passer
   `--madec-sidebar-bg` à `#313533`, `--madec-sidebar-item` à `#898fa9`
   et `--madec-sidebar-item-active` à `#fff`.
3. **Revenir au fond gris** : `body { background-color: var(--surface) }`.
