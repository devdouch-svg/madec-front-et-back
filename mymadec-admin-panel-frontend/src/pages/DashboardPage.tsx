import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link, useNavigate } from "react-router-dom";
import {
  ShoppingCart,
  Users,
  Package,
  Clock,
  Bell,
  Sparkles,
  ChevronRight,
  ChevronDown,
  CalendarRange,
  RefreshCw,
  Image,
  BookUser,
  Layers,
  AlertTriangle,
} from "lucide-react";
import api from "../lib/api";
import { fetchPromptinosStats } from "../lib/promptinos";
import type { DashboardData, DashboardPeriod } from "../lib/types";
import { PageLoader } from "../components/ui/Spinner";
import { PageHeader } from "../components/layout/PageHeader";
import { ErrorState } from "../components/ui/ErrorState";
import { StatusBadge } from "../components/ui/StatusBadge";
import { useAuth } from "../store/auth";
import { useRole } from "../lib/roles";
import { StaffScopeBanner } from "../components/staff/StaffScopeBanner";
import { RoleBadge } from "../components/ui/RoleBadge";
import { formatMAD, orderStatusLabel } from "../lib/labels";
import { mediaUrl } from "../lib/media";
import { format } from "date-fns";
import { fr } from "date-fns/locale";
import type { LucideIcon } from "lucide-react";
import { StatWidgetCard, StatusPie, RadialGauge, MarketOverviewChart, ActivityAreaChart, StatusColumnsChart, StatusProgressList } from "../components/dashboard/charts";
import { STATUS_CHART_COLORS, dailyCounts, dailySums } from "../components/dashboard/chartData";

/* ── Period filter ──────────────────────────────────────────────────────── */

const PERIOD_META: Record<
  DashboardPeriod,
  { option: string; caption: string; badge: string }
> = {
  week: { option: "Cette semaine", caption: "cette semaine", badge: "7 derniers jours" },
  last_week: { option: "Semaine dernière", caption: "semaine dernière", badge: "semaine dernière" },
  month: { option: "Ce mois", caption: "ce mois", badge: "ce mois" },
  last_month: { option: "Mois dernier", caption: "mois dernier", badge: "mois dernier" },
  year: { option: "Cette année", caption: "cette année", badge: "cette année" },
  custom: { option: "Personnalisé", caption: "période choisie", badge: "période choisie" },
};

/** ISO YYYY-MM-DD helpers for the native date inputs. */
function isoDay(d: Date): string {
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}
function firstOfMonthISO(): string {
  const d = new Date();
  return isoDay(new Date(d.getFullYear(), d.getMonth(), 1));
}
/** "2026-08-03" → "03/08/2026" for display. */
export function frDate(iso?: string): string {
  if (!iso) return "";
  const [y, m, d] = iso.split("-");
  return d && m && y ? `${d}/${m}/${y}` : iso;
}

function PeriodSelect({
  value,
  onChange,
  from,
  to,
  onFromChange,
  onToChange,
}: {
  value: DashboardPeriod;
  onChange: (p: DashboardPeriod) => void;
  from: string;
  to: string;
  onFromChange: (v: string) => void;
  onToChange: (v: string) => void;
}) {
  const dateInput =
    "h-9 rounded-lg border border-madec-border bg-white px-2.5 text-sm text-madec-text shadow-sm transition-colors hover:border-madec-primary focus:border-madec-primary focus:outline-none focus-visible:ring-2 focus-visible:ring-madec-primary/30";
  return (
    <div className="flex flex-wrap items-center gap-2">
      <div className="relative inline-flex items-center">
        <CalendarRange
          size={15}
          className="pointer-events-none absolute left-3 text-madec-primary"
        />
        <select
          value={value}
          onChange={(e) => onChange(e.target.value as DashboardPeriod)}
          aria-label="Filtrer par période"
          className="h-9 cursor-pointer appearance-none rounded-lg border border-madec-border bg-white pl-9 pr-9 text-sm font-medium text-madec-text shadow-sm transition-colors hover:border-madec-primary focus:border-madec-primary focus:outline-none focus-visible:ring-2 focus-visible:ring-madec-primary/30"
        >
          <option value="week">{PERIOD_META.week.option}</option>
          <option value="last_week">{PERIOD_META.last_week.option}</option>
          <option value="month">{PERIOD_META.month.option}</option>
          <option value="last_month">{PERIOD_META.last_month.option}</option>
          <option value="year">{PERIOD_META.year.option}</option>
          <option value="custom">{PERIOD_META.custom.option}</option>
        </select>
        <ChevronDown
          size={15}
          className="pointer-events-none absolute right-3 text-madec-muted"
        />
      </div>

      {value === "custom" && (
        <div className="flex items-center gap-1.5">
          <input
            type="date"
            value={from}
            max={to || undefined}
            onChange={(e) => onFromChange(e.target.value)}
            aria-label="Date de début"
            className={dateInput}
          />
          <span className="text-xs text-madec-muted">→</span>
          <input
            type="date"
            value={to}
            min={from || undefined}
            onChange={(e) => onToChange(e.target.value)}
            aria-label="Date de fin"
            className={dateInput}
          />
        </div>
      )}
    </div>
  );
}

/* ── Shared building blocks ─────────────────────────────────────────────── */

function QuickLink({
  to,
  icon: Icon,
  label,
  hint,
}: {
  to: string;
  icon: LucideIcon;
  label: string;
  hint?: string;
}) {
  return (
    <Link
      to={to}
      className="flex items-center gap-3 rounded-lg px-2 py-2.5 transition-colors hover:bg-madec-active"
    >
      <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-madec-tint text-madec-primary">
        <Icon size={16} strokeWidth={1.75} />
      </span>
      <span className="min-w-0 flex-1">
        <span className="block text-sm font-medium text-madec-text">{label}</span>
        {hint && <span className="block truncate text-xs text-madec-muted">{hint}</span>}
      </span>
      <ChevronRight size={16} className="shrink-0 text-madec-muted" />
    </Link>
  );
}

function PlafondGaugeCard({ plafond }: { plafond: DashboardData["plafond"] }) {
  if (!plafond.plafond_mensuel) {
    return (
      <div className="card h-full">
        <h2 className="mb-4 text-[15px] font-semibold text-madec-text">Plafond mensuel</h2>
        <p className="text-2xl font-bold text-madec-text">Illimité</p>
        <p className="mt-2 text-sm text-madec-muted">
          Dépensé ce mois :{" "}
          <strong className="text-madec-primary">{formatMAD(plafond.spent_this_month)}</strong>
        </p>
      </div>
    );
  }
  const pct = Math.min(100, (plafond.spent_this_month / plafond.plafond_mensuel) * 100);
  const gaugeColor = pct > 90 ? "#fd625e" : pct > 70 ? "#ffbf53" : "#5156be";
  return (
    <div className="card h-full">
      <h2 className="mb-1 text-[15px] font-semibold text-madec-text">Plafond mensuel</h2>
      <RadialGauge percent={pct} label="Utilisé" color={gaugeColor} />
      <div className="mt-1 grid grid-cols-2 gap-2">
        <div>
          <p className="mb-1 text-[11px] uppercase text-madec-muted">Dépensé</p>
          <h5 className="text-sm font-semibold text-madec-text">{formatMAD(plafond.spent_this_month)}</h5>
        </div>
        <div>
          <p className="mb-1 text-[11px] uppercase text-madec-muted">Restant</p>
          <h5 className="text-sm font-semibold text-madec-text">{formatMAD(plafond.remaining ?? 0)}</h5>
        </div>
      </div>
    </div>
  );
}

/* ── "Wallet Balance" card → répartition des commandes ───────────────────── */

function OrdersPieCard({ entries }: { entries: [string, number][] }) {
  const withLabels: [string, number, string][] = entries.map(([s, n]) => [s, n, orderStatusLabel(s)]);
  return (
    <div className="card !p-4">
      <div className="mb-3 flex flex-wrap items-center">
        <h2 className="mr-2 text-sm font-semibold text-madec-text">Commandes par statut</h2>
        <Link to="/orders" className="link-brand ml-auto text-xs">
          Voir tout
        </Link>
      </div>
      {entries.length === 0 ? (
        <p className="py-6 text-center text-sm text-madec-muted">Aucune commande</p>
      ) : (
        <>
          <StatusPie entries={withLabels} />
          <ul className="mt-3 grid grid-cols-2 gap-x-2">
            {withLabels.map(([status, count, label]) => (
              <li key={status}>
                <Link
                  to={`/orders?status=${encodeURIComponent(status)}`}
                  className="flex items-center justify-between gap-1 rounded px-1.5 py-1 transition-colors hover:bg-madec-active"
                >
                  <span className="flex min-w-0 items-center gap-1.5 text-xs text-madec-secondary">
                    <span
                      className="inline-block h-2 w-2 shrink-0 rounded-full"
                      style={{ backgroundColor: STATUS_CHART_COLORS[status] ?? "#a8aada" }}
                    />
                    <span className="truncate">{label}</span>
                  </span>
                  <span className="text-xs font-semibold text-madec-text">{count}</span>
                </Link>
              </li>
            ))}
          </ul>
        </>
      )}
    </div>
  );
}

function RecentOrdersTable({
  orders,
  showBuyer = false,
}: {
  orders: DashboardData["recent_orders"];
  showBuyer?: boolean;
}) {
  const navigate = useNavigate();

  if (orders.length === 0) {
    return <p className="py-6 text-center text-sm text-madec-muted">Aucune commande récente</p>;
  }
  return (
    <div className="overflow-x-auto">
      <table className="data-table !border-0 !shadow-none">
        <thead>
          <tr>
            <th>Référence</th>
            {showBuyer && <th>Acheteur</th>}
            <th>Date</th>
            <th>Statut</th>
            <th className="text-right">Montant</th>
          </tr>
        </thead>
        <tbody>
          {orders.map((o) => (
            <tr
              key={o.id}
              className="cursor-pointer"
              onClick={() => navigate(`/orders?order=${o.id}`)}
            >
              <td className="font-medium text-madec-text">{o.sorder_code}</td>
              {showBuyer && (
                <td className="text-madec-secondary">{o.buyer_name ?? "—"}</td>
              )}
              <td className="text-madec-muted">
                {format(new Date(o.created_at), "d MMM yyyy", { locale: fr })}
              </td>
              <td>
                <StatusBadge status={o.sorder_status} />
              </td>
              <td className="text-right font-semibold text-madec-primary">{formatMAD(o.dueamount)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

/* ── Admin / gestionnaire dashboard ─────────────────────────────────────── */

function StaffDashboard({
  data,
  isAdmin,
  meta,
}: {
  data: DashboardData;
  isAdmin: boolean;
  meta: { caption: string; badge: string };
}) {
  const stats = data.admin_stats!;
  const pending = stats.pending_orders ?? 0;
  const uncategorized = stats.uncategorized_mobile_products ?? 0;
  const statusEntries = Object.entries(stats.orders_by_status ?? {}).filter(([, n]) => n > 0);

  const adminLinks = [
    { to: "/orders?status=pending", icon: Clock, label: "Commandes en attente", hint: pending > 0 ? `${pending} avant ETL` : "Aucune en attente" },
    { to: "/orders", icon: ShoppingCart, label: "Toutes les commandes", hint: "Suivi des statuts" },
    { to: "/products", icon: Package, label: "Catalogue produits", hint: `${stats.active_products} actifs` },
    { to: "/catalog", icon: Layers, label: "Référentiels", hint: "ERP et catégories mobile" },
    { to: "/users", icon: Users, label: "Utilisateurs", hint: `${stats.active_users} actifs` },
    ...(isAdmin
      ? [
          { to: "/sync", icon: RefreshCw, label: "Sync ETL", hint: "Serveur intermédiaire" },
          { to: "/banners", icon: Image, label: "Bannières mobile", hint: "Accueil application" },
          { to: "/annuaire", icon: BookUser, label: "Annuaire", hint: "Contacts MADEC" },
        ]
      : []),
    { to: "/promptinos", icon: Sparkles, label: "Promptinos", hint: "Gamme dédiée" },
  ];

  // Activity series for the selected period (backend-provided). Falls back to
  // client-side sparklines from recent orders if the API omits the series.
  const series = stats.series ?? [];
  const hasSeries = series.length > 0;
  const seriesLabels = hasSeries ? series.map((s) => s.label) : undefined;
  const countSpark = hasSeries
    ? series.map((s) => s.count)
    : dailyCounts(data.recent_orders.map((o) => o.created_at));
  const revenueSpark = hasSeries
    ? series.map((s) => s.amount)
    : dailySums(data.recent_orders.map((o) => [o.created_at, o.dueamount]));
  const statusSpark = statusEntries.map(([, n]) => n);

  return (
    <div className="space-y-6">
      {/* KPIs — Minia widget cards */}
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatWidgetCard
          label="Chiffre d'affaires"
          value={formatMAD(stats.revenue_this_month)}
          rawValue={stats.revenue_this_month}
          formatValue={formatMAD}
          icon={ShoppingCart}
          iconTone="success"
          spark={revenueSpark}
          badge={`${stats.orders_this_month} commande${stats.orders_this_month > 1 ? "s" : ""}`}
          badgeTone="success"
          caption={meta.caption}
          href="/orders"
        />
        <StatWidgetCard
          label="Commandes"
          value={stats.orders_this_month}
          rawValue={stats.orders_this_month}
          icon={Package}
          iconTone="primary"
          spark={countSpark}
          badge={meta.badge}
          badgeTone="primary"
          caption="activité"
          href="/orders"
        />
        <StatWidgetCard
          label="En attente"
          value={pending}
          rawValue={pending}
          icon={Clock}
          iconTone={pending > 0 ? "warning" : "success"}
          spark={statusSpark}
          badge={pending > 0 ? "Avant ETL" : "Aucune"}
          badgeTone={pending > 0 ? "warning" : "success"}
          caption={pending > 0 ? "pas encore prises par l'ETL" : "tout est à jour"}
          href="/orders?status=pending"
        />
        <StatWidgetCard
          label={isAdmin ? "Utilisateurs actifs" : "Produits actifs"}
          value={isAdmin ? stats.active_users : stats.active_products}
          rawValue={isAdmin ? stats.active_users : stats.active_products}
          icon={isAdmin ? Users : Package}
          iconTone="neutral"
          badge={isAdmin ? `${stats.active_products} produits` : `${stats.active_users} utilisateurs`}
          badgeTone="neutral"
          caption="actifs"
          href={isAdmin ? "/users" : "/products"}
        />
      </div>

      {/* Alerts */}
      {uncategorized > 0 && (
        <Link
          to="/products?missing_mobile_category=true"
          className="flex items-center gap-3 rounded-lg border border-amber-200 bg-amber-50/60 px-4 py-3 transition-colors hover:bg-amber-50"
        >
          <AlertTriangle size={18} className="shrink-0 text-amber-600" />
          <div className="min-w-0 flex-1">
            <p className="text-sm font-medium text-madec-text">
              {uncategorized} produit{uncategorized > 1 ? "s" : ""} sans catégorie mobile
            </p>
            <p className="text-xs text-madec-muted">Cliquer pour les assigner dans le catalogue</p>
          </div>
          <ChevronRight size={16} className="text-madec-muted" />
        </Link>
      )}

      {/* Minia-style diagrams */}
      <div className="grid gap-4 lg:grid-cols-3">
        <div className="card lg:col-span-2 !p-4">
          <div className="mb-2 flex flex-wrap items-center gap-2">
            <h2 className="text-sm font-semibold text-madec-text">Vue d&apos;activité</h2>
            <span className="text-xs text-madec-muted">{meta.badge}</span>
            <Link to="/orders" className="link-brand ml-auto text-xs">
              Voir tout
            </Link>
          </div>
          <ActivityAreaChart counts={countSpark} amounts={revenueSpark} categories={seriesLabels} />
        </div>

        <div className="card !p-4">
          <div className="mb-3 flex items-center justify-between gap-2">
            <h2 className="text-sm font-semibold text-madec-text">Répartition</h2>
            <Link to="/orders" className="link-brand text-xs">
              Détail
            </Link>
          </div>
          {statusEntries.length === 0 ? (
            <p className="py-10 text-center text-sm text-madec-muted">Aucune donnée</p>
          ) : (
            <StatusProgressList
              entries={statusEntries.map(([s, n]) => [s, n, orderStatusLabel(s)])}
            />
          )}
        </div>
      </div>

      <div className="grid gap-4 lg:grid-cols-5">
        <div className="card lg:col-span-3 !p-4">
          <div className="mb-2 flex flex-wrap items-center gap-2">
            <h2 className="text-sm font-semibold text-madec-text">Market Overview</h2>
            <span className="text-xs text-madec-muted">Commandes vs CA</span>
          </div>
          <MarketOverviewChart counts={countSpark} amounts={revenueSpark} categories={seriesLabels} />
        </div>

        <div className="card lg:col-span-2 !p-4">
          <div className="mb-2 flex items-center justify-between gap-2">
            <h2 className="text-sm font-semibold text-madec-text">Statuts</h2>
          </div>
          {statusEntries.length === 0 ? (
            <p className="py-10 text-center text-sm text-madec-muted">Aucune commande</p>
          ) : (
            <StatusColumnsChart
              entries={statusEntries.map(([s, n]) => [s, n, orderStatusLabel(s)])}
            />
          )}
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Recent orders */}
        <div className="card lg:col-span-2">
          <div className="mb-4 flex items-center justify-between gap-2">
            <h2 className="text-sm font-semibold text-madec-text">Dernières commandes</h2>
            <Link to="/orders" className="link-brand text-xs">
              Voir tout
            </Link>
          </div>
          <RecentOrdersTable orders={data.recent_orders} showBuyer />
        </div>

        {/* Sidebar */}
        <div className="space-y-4">
          <OrdersPieCard entries={statusEntries} />

          <div className="card">
            <h2 className="mb-1 text-sm font-semibold text-madec-text">Accès rapide</h2>
            <p className="mb-2 text-xs text-madec-muted">Navigation directe</p>
            <nav className="-mx-2 flex flex-col">
              {adminLinks.map((item) => (
                <QuickLink key={item.to + item.label} {...item} />
              ))}
            </nav>
          </div>
        </div>
      </div>

      {/* Banners — admin only, compact */}
      {isAdmin && data.banners.length > 0 && (
        <div className="card">
          <div className="mb-3 flex items-center justify-between">
            <h2 className="text-sm font-semibold text-madec-text">Bannières actives</h2>
            <Link to="/banners" className="link-brand text-xs">
              Gérer
            </Link>
          </div>
          <div className="flex gap-3 overflow-x-auto pb-1">
            {data.banners.slice(0, 4).map((b) => (
              <div
                key={b.id}
                className="w-48 shrink-0 overflow-hidden rounded-lg border border-madec-border bg-white"
              >
                {b.image_path ? (
                  <img
                    src={mediaUrl(b.image_path, b.updated_at)}
                    alt={b.title ?? ""}
                    className="h-24 w-full object-cover"
                  />
                ) : (
                  <div className="flex h-24 items-center justify-center bg-madec-tint text-madec-muted">
                    <Image size={20} />
                  </div>
                )}
                <p className="truncate px-2 py-2 text-xs font-medium text-madec-text">{b.title ?? "—"}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

/* ── Acheteur dashboard ─────────────────────────────────────────────────── */

function BuyerDashboard({ data, promptinosTotal }: { data: DashboardData; promptinosTotal: number }) {
  return (
    <div className="space-y-6">
      {promptinosTotal > 0 && (
        <Link
          to="/promptinos"
          className="group flex items-center justify-between gap-4 rounded-xl border border-madec-border bg-white p-4 transition-colors hover:border-madec-primary/30 hover:bg-madec-active/40"
        >
          <div className="flex items-center gap-3">
            <span className="flex h-10 w-10 items-center justify-center rounded-lg bg-madec-tint text-madec-primary">
              <Sparkles size={20} />
            </span>
            <div>
              <p className="text-sm font-semibold text-madec-text">Promptinos</p>
              <p className="text-xs text-madec-muted">{promptinosTotal} produits — gamme dédiée</p>
            </div>
          </div>
          <ChevronRight size={18} className="text-madec-muted transition-transform group-hover:translate-x-0.5" />
        </Link>
      )}

      {/* Minia widget cards */}
      <div className="grid gap-4 sm:grid-cols-3">
        <StatWidgetCard
          label="Dépensé ce mois"
          value={formatMAD(data.plafond.spent_this_month)}
          rawValue={data.plafond.spent_this_month}
          formatValue={formatMAD}
          icon={ShoppingCart}
          iconTone="primary"
          spark={dailySums(data.recent_orders.map((o) => [o.created_at, o.dueamount]))}
          badge={data.plafond.plafond_mensuel ? "Plafond suivi" : "Illimité"}
          badgeTone="primary"
          caption="achats du mois"
        />
        <StatWidgetCard
          label="Commandes récentes"
          value={data.recent_orders.length}
          rawValue={data.recent_orders.length}
          icon={Package}
          iconTone="neutral"
          spark={dailyCounts(data.recent_orders.map((o) => o.created_at))}
          badge="14 derniers jours"
          badgeTone="neutral"
          caption="activité"
          href="/orders"
        />
        <StatWidgetCard
          label="Notifications"
          value={data.unread_notifications}
          rawValue={data.unread_notifications}
          icon={Bell}
          iconTone={data.unread_notifications > 0 ? "warning" : "success"}
          badge={data.unread_notifications > 0 ? "Non lues" : "À jour"}
          badgeTone={data.unread_notifications > 0 ? "warning" : "success"}
          caption="boîte de réception"
          href="/notifications"
        />
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <PlafondGaugeCard plafond={data.plafond} />
        <div className="card lg:col-span-2">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-sm font-semibold text-madec-text">Mes dernières commandes</h2>
            <Link to="/orders" className="link-brand text-xs">
              Voir tout
            </Link>
          </div>
          <RecentOrdersTable orders={data.recent_orders} />
        </div>
      </div>

      {data.mobile_catalog.length > 0 && (
        <div className="card">
          <div className="mb-3 flex items-center justify-between">
            <h2 className="text-sm font-semibold text-madec-text">Catégories</h2>
            <Link to="/products" className="link-brand text-xs">
              Catalogue
            </Link>
          </div>
          <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
            {data.mobile_catalog.slice(0, 8).map((cat) => (
              <Link
                key={cat.id}
                to={`/products?categorie=${encodeURIComponent(cat.name)}`}
                className="flex items-center gap-2.5 rounded-lg border border-madec-border p-2 transition-colors hover:bg-madec-active"
              >
                {cat.image_path ? (
                  <img
                    src={mediaUrl(cat.image_path, cat.updated_at)}
                    alt=""
                    className="h-10 w-10 shrink-0 rounded-md object-cover"
                  />
                ) : (
                  <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-md bg-madec-tint text-madec-primary">
                    <Package size={16} />
                  </div>
                )}
                <div className="min-w-0">
                  <p className="truncate text-sm font-medium text-madec-text">{cat.name}</p>
                  <p className="text-xs text-madec-muted">{cat.product_count} produit(s)</p>
                </div>
              </Link>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

/* ── Page ───────────────────────────────────────────────────────────────── */

export function DashboardPage() {
  const { user } = useAuth();
  const { isAdmin, isGest, isStaff, role } = useRole();
  const [period, setPeriod] = useState<DashboardPeriod>("month");
  const [customFrom, setCustomFrom] = useState(firstOfMonthISO);
  const [customTo, setCustomTo] = useState(() => isoDay(new Date()));

  const isCustom = period === "custom";
  const customReady = !isCustom || (!!customFrom && !!customTo);

  const subtitle = isAdmin
    ? "Vue d'ensemble de la plateforme"
    : isGest
      ? "Suivi des commandes et du catalogue"
      : "Votre activité et commandes";

  const { data, isLoading, isError, refetch } = useQuery<DashboardData>({
    queryKey: ["dashboard", period, isCustom ? customFrom : null, isCustom ? customTo : null],
    queryFn: () =>
      api
        .get("/dashboard", {
          params: {
            period,
            ...(isCustom ? { date_from: customFrom, date_to: customTo } : {}),
          },
        })
        .then((r) => r.data),
    enabled: customReady,
  });

  const { data: promptinosStats } = useQuery({
    queryKey: ["promptinos", "stats"],
    queryFn: fetchPromptinosStats,
    staleTime: 60_000,
  });

  if (isLoading) return <PageLoader />;
  if (isError || !data) {
    return (
      <div className="page-content max-w-7xl">
        <PageHeader title="Tableau de bord" subtitle="Vue d'ensemble" />
        <ErrorState onRetry={() => refetch()} />
      </div>
    );
  }

  const firstName = data.user.full_name?.split(" ")[0] ?? user?.email;

  // Period label — for "custom", derive it from the range the backend resolved.
  const baseMeta = PERIOD_META[period];
  const meta =
    isCustom && data.admin_stats?.range_from && data.admin_stats?.range_to
      ? {
          caption: `du ${frDate(data.admin_stats.range_from)} au ${frDate(data.admin_stats.range_to)}`,
          badge: `${frDate(data.admin_stats.range_from)} → ${frDate(data.admin_stats.range_to)}`,
        }
      : baseMeta;

  return (
    <div className="page-content max-w-7xl">
      <PageHeader
        title={`Bonjour, ${firstName}`}
        subtitle={subtitle}
        actions={
          <div className="flex flex-wrap items-center gap-2">
            {isStaff && (
              <PeriodSelect
                value={period}
                onChange={setPeriod}
                from={customFrom}
                to={customTo}
                onFromChange={setCustomFrom}
                onToChange={setCustomTo}
              />
            )}
            {role && <RoleBadge role={role} />}
            {data.unread_notifications > 0 && (
              <Link to="/notifications" className="btn-primary btn-sm">
                <Bell size={14} />
                {data.unread_notifications} notification{data.unread_notifications > 1 ? "s" : ""}
              </Link>
            )}
          </div>
        }
      />

      {isGest && role && <StaffScopeBanner page="dashboard" role={role} />}

      {isStaff && data.admin_stats ? (
        <StaffDashboard data={data} isAdmin={isAdmin} meta={meta} />
      ) : (
        <BuyerDashboard data={data} promptinosTotal={promptinosStats?.total ?? 0} />
      )}
    </div>
  );
}
