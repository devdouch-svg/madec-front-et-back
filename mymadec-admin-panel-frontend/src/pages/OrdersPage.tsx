import { useState, useEffect } from "react";
import { useSearchParams } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Plus, XCircle, ShoppingBag, Banknote, CreditCard, Calendar, Building2, ChevronRight, Download } from "lucide-react";
import api from "../lib/api";
import { getErrorMessage, isPlafondError } from "../lib/errors";
import type { Order, OrderLine, OrderStatusHistory, PaginatedResponse } from "../lib/types";
import { PageLoader } from "../components/ui/Spinner";
import { StatusBadge } from "../components/ui/StatusBadge";
import { Pagination } from "../components/ui/Pagination";
import { Modal } from "../components/ui/Modal";
import { FilterChips } from "../components/ui/FilterChips";
import { EmptyState } from "../components/ui/EmptyState";
import { ErrorState } from "../components/ui/ErrorState";
import { formatMAD, orderStatusLabel, paymentModeLabel, PAYMENT_LABELS } from "../lib/labels";
import { useAuth } from "../store/auth";
import { useRole } from "../lib/roles";
import { staffPageScope } from "../lib/staffCapabilities";
import { useCart } from "../store/cart";
import toast from "react-hot-toast";
import { format } from "date-fns";
import { fr } from "date-fns/locale";

const STATUS_OPTIONS = ["", "pending", "validated", "processing", "ready", "delivered", "cancelled"] as const;
const ORDER_PAGE_SIZE = 15;
const STATUS_FILTERS = STATUS_OPTIONS.map((s) => ({
  value: s,
  label: s ? orderStatusLabel(s) : "Tous",
}));
function CartDrawer({ onClose }: { onClose: () => void }) {
  const { items, remove, setQty, total, clear } = useCart();
  const qc = useQueryClient();
  const { user } = useAuth();
  const [notes, setNotes] = useState("");
  const needsPaymentChoice = user?.payment_mode === "les_deux";
  const [paymentMode, setPaymentMode] = useState<"especes" | "carte">("especes");

  const create = useMutation({
    mutationFn: () =>
      api.post("/orders", {
        lines: items.map((i) => ({ product_code: i.product.product_code, quantity: i.quantity })),
        notes: notes.trim() || undefined,
        ...(needsPaymentChoice ? { payment_mode: paymentMode } : {}),
      }),
    onSuccess: () => {
      toast.success("Commande passée !");
      clear();
      onClose();
      qc.invalidateQueries({ queryKey: ["orders"] });
      qc.invalidateQueries({ queryKey: ["dashboard"] });
    },
    onError: (e: any) => {
      if (isPlafondError(e)) {
        const p = e.response.data.detail;
        toast.error(`Plafond dépassé — disponible : ${formatMAD(p.available)}, demandé : ${formatMAD(p.requested)}`);
      } else {
        toast.error(getErrorMessage(e, "Erreur lors de la commande"));
      }
    },
  });

  if (items.length === 0)
    return <p className="py-8 text-center text-sm text-madec-muted">Votre panier est vide — ajoutez des produits depuis le catalogue.</p>;

  return (
    <div className="space-y-3">
      {items.map((item) => (
        <div key={item.product.id} className="flex items-center gap-3">
          <div className="flex-1 min-w-0">
            <p className="truncate text-sm font-medium text-madec-text">{item.product.name}</p>
            <p className="text-xs text-madec-muted">{formatMAD(item.product.final_price ?? 0)} / unité TTC</p>
          </div>
          <div className="flex items-center gap-2">
            <input
              type="number" min={0.001} step="0.001" value={item.quantity}
              onChange={(e) => setQty(item.product.id, parseFloat(e.target.value) || 1)}
              className="input w-20 text-center py-1"
            />
            <button
              type="button"
              onClick={() => remove(item.product.id)}
              className="text-red-400 hover:text-red-600"
              aria-label={`Retirer ${item.product.name}`}
            >
              <XCircle size={16} />
            </button>
          </div>
        </div>
      ))}
      {needsPaymentChoice && (
        <div>
          <p className="label mb-2">Mode de paiement pour cette commande</p>
          <div className="flex gap-2">
            {(["especes", "carte"] as const).map((mode) => (
              <button
                key={mode}
                type="button"
                onClick={() => setPaymentMode(mode)}
                className={`flex flex-1 items-center justify-center gap-2 rounded-xl border-2 py-2.5 text-sm font-medium transition-colors ${
                  paymentMode === mode
                    ? "border-madec-primary bg-madec-active text-madec-primary"
                    : "border-madec-border bg-white text-madec-secondary hover:border-madec-tint"
                }`}
              >
                {mode === "especes" ? <Banknote size={16} /> : <CreditCard size={16} />}
                {PAYMENT_LABELS[mode]}
              </button>
            ))}
          </div>
        </div>
      )}
      <div>
        <label className="label" htmlFor="cart-notes">Notes (optionnel)</label>
        <textarea
          id="cart-notes"
          className="input"
          rows={2}
          placeholder="Instructions pour la commande..."
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
        />
      </div>
      <div className="border-t pt-3 flex items-center justify-between">
        <div>
          <p className="text-xs text-madec-muted">
            Mode paiement :{" "}
            <strong>
              {needsPaymentChoice
                ? PAYMENT_LABELS[paymentMode]
                : user?.payment_mode
                  ? paymentModeLabel(user.payment_mode)
                  : "—"}
            </strong>
          </p>
          <p className="text-base font-bold text-madec-text">Total CMD : {formatMAD(total())}</p>
        </div>
        <button type="button" onClick={() => create.mutate()} disabled={create.isPending} className="btn-primary">
          {create.isPending ? "..." : "Confirmer"}
        </button>
      </div>
    </div>
  );
}

function OrderDetailPanel({ orderId, onClose }: { orderId: number; onClose: () => void }) {
  const qc = useQueryClient();
  const { isAdmin, isGest, isAdminOrGest, isAcheteur } = useRole();

  const { data: order, isLoading } = useQuery<Order>({
    queryKey: ["order", orderId],
    queryFn: () => api.get(`/orders/${orderId}`).then((r) => r.data),
  });

  const { data: lines } = useQuery<OrderLine[]>({
    queryKey: ["order-lines", orderId],
    queryFn: () => api.get(`/orders/${orderId}/lines`).then((r) => r.data),
  });

  const { data: history } = useQuery<OrderStatusHistory[]>({
    queryKey: ["order-history", orderId],
    queryFn: () => api.get(`/orders/${orderId}/status-history`).then((r) => r.data),
  });

  const invalidate = () => {
    qc.invalidateQueries({ queryKey: ["orders"] });
    qc.invalidateQueries({ queryKey: ["order", orderId] });
    qc.invalidateQueries({ queryKey: ["order-lines", orderId] });
    qc.invalidateQueries({ queryKey: ["order-history", orderId] });
    qc.invalidateQueries({ queryKey: ["dashboard"] });
  };

  const cancel = useMutation({
    mutationFn: () => api.patch(`/orders/${orderId}/cancel`),
    onSuccess: () => { toast.success("Commande annulée"); invalidate(); onClose(); },
    onError: (e) => toast.error(getErrorMessage(e, "Impossible d'annuler")),
  });

  const refreshBl = useMutation({
    mutationFn: () => api.get(`/orders/${orderId}/bl`),
    onSuccess: () => { toast.success("Données BL actualisées"); invalidate(); },
    onError: (e) => toast.error(getErrorMessage(e, "Erreur BL")),
  });

  if (isLoading || !order) return <PageLoader />;

  // Cancel only before ETL push (pending / legacy validated without pushed_at)
  const awaitingEtl =
    !order.pushed_at &&
    (order.sorder_status === "pending" || order.sorder_status === "validated");
  const canCancel = awaitingEtl && (isAcheteur || isAdmin);

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-3 text-sm">
        <div><span className="text-madec-muted">Code :</span> <strong>{order.sorder_code}</strong></div>
        <div><span className="text-madec-muted">Statut :</span> <StatusBadge status={order.sorder_status} /></div>
        <div><span className="text-madec-muted">Paiement :</span> {paymentModeLabel(order.payment_mode)}</div>
        <div>
          <span className="text-madec-muted">Montant à payer :</span>{" "}
          <strong className="text-madec-primary">
            {formatMAD(Number(order.bl_amount != null ? order.bl_amount : order.dueamount))}
          </strong>
        </div>
        {Number(order.discount_total) > 0 && (
          <div><span className="text-madec-muted">Remise :</span> -{formatMAD(Number(order.discount_total))}</div>
        )}
        {Number(order.fixedtax) > 0 && (
          <div><span className="text-madec-muted">Frais fixes :</span> {formatMAD(Number(order.fixedtax))}</div>
        )}
        {order.bl_amount != null ? (
          <div><span className="text-madec-muted">Montant BL :</span> {formatMAD(Number(order.bl_amount))}</div>
        ) : (
          <div><span className="text-madec-muted">Montant commande :</span> {formatMAD(Number(order.dueamount))}</div>
        )}
        {order.agence && (
          <div><span className="text-madec-muted">Agence :</span> {order.agence}</div>
        )}
        {order.pushed_at && (
          <div><span className="text-madec-muted">Envoyé ERP :</span> {format(new Date(order.pushed_at), "d MMM yyyy HH:mm", { locale: fr })}</div>
        )}
        {order.notes && <div className="col-span-2"><span className="text-madec-muted">Notes :</span> {order.notes}</div>}
      </div>

      <div>
        <p className="mb-2 text-sm font-semibold text-madec-text">Lignes de commande</p>
        <div className="overflow-x-auto rounded-lg border border-madec-border">
          <table className="data-table !rounded-lg !border-0 !shadow-none">
          <thead className="text-xs text-madec-muted border-b">
            <tr>
              <th className="text-left py-1">Produit</th>
              <th className="text-right py-1">Qté</th>
              <th className="text-right py-1">BL</th>
              <th className="text-right py-1">P.U. TTC</th>
              <th className="text-right py-1">Total</th>
            </tr>
          </thead>
          <tbody>
            {(lines ?? []).map((l) => (
              <tr key={l.id} className="border-b last:border-0">
                <td className="py-1.5">{l.product_name}</td>
                <td className="text-right">{l.quantity}</td>
                <td className="text-right text-madec-muted">{l.bl_quantity ?? "—"}</td>
                <td className="text-right">{formatMAD(Number(l.unit_price))}</td>
                <td className="text-right font-medium">{formatMAD(Number(l.line_amount))}</td>
              </tr>
            ))}
          </tbody>
          </table>
        </div>
      </div>

      {(history ?? []).length > 0 && (
        <div>
          <p className="text-sm font-semibold text-madec-text mb-2">Historique</p>
          <div className="space-y-1">
            {history?.map((h) => (
              <div key={h.id} className="flex items-center gap-2 text-xs text-madec-secondary">
                <StatusBadge status={h.status} />
                <span>{format(new Date(h.created_at), "d MMM yyyy HH:mm", { locale: fr })}</span>
                {h.notes && <span className="text-madec-muted">— {h.notes}</span>}
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="flex flex-wrap gap-2 justify-end pt-2 border-t">
        {isAdminOrGest && (
          <button
            onClick={() => refreshBl.mutate()}
            disabled={refreshBl.isPending}
            className="btn-secondary btn-sm"
          >
            Actualiser BL
          </button>
        )}
        {canCancel && (
          <button onClick={() => cancel.mutate()} disabled={cancel.isPending} className="btn-danger btn-sm">
            Annuler
          </button>
        )}
      </div>
    </div>
  );
}

export function OrdersPage() {
  const { user } = useAuth();
  const [searchParams, setSearchParams] = useSearchParams();
  const [page, setPage]           = useState(1);
  const [status, setStatus]       = useState(() => searchParams.get("status") ?? "");
  const [societyCode, setSociety] = useState("");
  const [paymentMode, setPaymentModeFilter] = useState(() => searchParams.get("payment_mode") ?? "");
  const [dateFrom, setDateFrom]   = useState("");
  const [dateTo, setDateTo]       = useState("");
  const [selectedId, setSelectedId] = useState<number | null>(() => {
    const id = Number(searchParams.get("order"));
    return Number.isFinite(id) && id > 0 ? id : null;
  });
  const [cartOpen, setCartOpen]   = useState(false);
  const { count } = useCart();
  const { isAdminOrGest, isGest, isAcheteur, role } = useRole();

  const closeOrderDetail = () => {
    setSelectedId(null);
    if (searchParams.get("order")) {
      const params = new URLSearchParams(searchParams);
      params.delete("order");
      setSearchParams(params, { replace: true });
    }
  };

  useEffect(() => {
    const id = Number(searchParams.get("order"));
    if (Number.isFinite(id) && id > 0) {
      setSelectedId(id);
    }
  }, [searchParams]);

  const ordersEndpoint = isAcheteur ? "/orders/me" : "/orders";
  const ordersSubtitle = isAcheteur
    ? "Vos commandes et panier"
    : staffPageScope("orders", role) ?? "Suivi et traitement des commandes";

  const statusFilters = isGest
    ? STATUS_FILTERS.filter((f) => f.value !== "cancelled")
    : STATUS_FILTERS;

  const buildQs = () => {
    const params = new URLSearchParams({
      page: String(page),
      page_size: String(ORDER_PAGE_SIZE),
    });
    if (status)     params.set("status",      status);
    if (societyCode) params.set("society_code", societyCode);
    if (paymentMode) params.set("payment_mode", paymentMode);
    if (dateFrom)   params.set("date_from",   dateFrom);
    if (dateTo)     params.set("date_to",     dateTo);
    return params.toString();
  };

  const { data, isLoading, isError, refetch } = useQuery<PaginatedResponse<Order>>({
    queryKey: ["orders", page, status, societyCode, paymentMode, dateFrom, dateTo, user?.role],
    queryFn: () => api.get(`${ordersEndpoint}?${buildQs()}`).then((r) => r.data),
  });

  const hasFilters = !!(status || societyCode || paymentMode || dateFrom || dateTo);

  const clearFilters = () => {
    setStatus("");
    setSociety("");
    setPaymentModeFilter("");
    setDateFrom("");
    setDateTo("");
    setPage(1);
  };

  const exportOrders = async (format: "csv" | "xlsx" | "pdf") => {
    try {
      const params = new URLSearchParams({ format });
      if (status)      params.set("status",       status);
      if (societyCode) params.set("society_code", societyCode);
      if (paymentMode) params.set("payment_mode", paymentMode);
      if (dateFrom)    params.set("date_from",    dateFrom);
      if (dateTo)      params.set("date_to",      dateTo);
      const r = await api.get(`/orders/export?${params}`, { responseType: "blob" });
      const url = URL.createObjectURL(r.data as Blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `commandes.${format}`;
      a.click();
      URL.revokeObjectURL(url);
      toast.success("Export téléchargé");
    } catch (e) {
      toast.error(getErrorMessage(e, "Export impossible"));
    }
  };

  if (isLoading && !data) return <PageLoader />;

  return (
    <div className="page-content max-w-7xl space-y-6">
      <section className="page-hero">
        <div className="page-hero-bg" aria-hidden />
        <div className="page-hero-inner">
          <div className="min-w-0">
            <span className="page-hero-icon" aria-hidden>
              <ShoppingBag size={18} />
            </span>
            <h1 className="page-hero-title">Commandes</h1>
            <p className="page-hero-subtitle">{ordersSubtitle}</p>
          </div>
          {isAcheteur && (
            <button type="button" className="btn-primary relative shrink-0" onClick={() => setCartOpen(true)}>
              <Plus size={16} /> Nouvelle commande
              {count() > 0 && (
                <span className="absolute -right-1.5 -top-1.5 flex h-5 min-w-5 items-center justify-center rounded-full bg-red-500 px-1 text-[10px] font-bold text-white">
                  {count()}
                </span>
              )}
            </button>
          )}
        </div>
      </section>

      <div className="catalog-toolbar">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <p className="text-sm font-semibold text-madec-text">Filtrer les commandes</p>
          <div className="flex items-center gap-3">
            {hasFilters && (
              <button type="button" onClick={clearFilters} className="link-brand text-xs">
                Réinitialiser les filtres
              </button>
            )}
            <div className="flex items-center gap-1.5">
              <Download size={14} className="text-madec-muted" />
              <span className="text-xs text-madec-muted">Exporter :</span>
              <button type="button" onClick={() => exportOrders("csv")} className="btn-secondary btn-sm">CSV</button>
              <button type="button" onClick={() => exportOrders("xlsx")} className="btn-secondary btn-sm">Excel</button>
              <button type="button" onClick={() => exportOrders("pdf")} className="btn-secondary btn-sm">PDF</button>
            </div>
          </div>
        </div>

        <FilterChips
          options={statusFilters}
          value={status}
          onChange={(s) => { setStatus(s); setPage(1); }}
        />

        {isAdminOrGest && (
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <div className="relative sm:col-span-2 lg:col-span-1">
              <Building2 size={16} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-madec-muted" />
              <input
                type="text"
                className="input pl-9"
                placeholder="Code société…"
                value={societyCode}
                onChange={(e) => { setSociety(e.target.value); setPage(1); }}
              />
            </div>
            <select
              className="input"
              value={paymentMode}
              onChange={(e) => { setPaymentModeFilter(e.target.value); setPage(1); }}
              aria-label="Mode de paiement"
            >
              <option value="">Tous paiements</option>
              <option value="especes">{PAYMENT_LABELS.especes}</option>
              <option value="carte">{PAYMENT_LABELS.carte}</option>
              <option value="deduction_salaire">{PAYMENT_LABELS.deduction_salaire}</option>
            </select>
            <div className="relative">
              <Calendar size={16} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-madec-muted" />
              <input
                type="date"
                className="input pl-9"
                value={dateFrom}
                onChange={(e) => { setDateFrom(e.target.value); setPage(1); }}
                aria-label="Date de début"
              />
            </div>
            <div className="relative">
              <Calendar size={16} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-madec-muted" />
              <input
                type="date"
                className="input pl-9"
                value={dateTo}
                onChange={(e) => { setDateTo(e.target.value); setPage(1); }}
                aria-label="Date de fin"
              />
            </div>
          </div>
        )}
      </div>

      {isError && <ErrorState onRetry={() => refetch()} />}

      {!isError && data && data.items.length === 0 && (
        <EmptyState
          icon={ShoppingBag}
          title="Aucune commande"
          description={status ? "Aucun résultat pour ce filtre." : "Les commandes apparaîtront ici une fois créées."}
          action={
            status ? (
              <button type="button" className="btn-secondary" onClick={() => { setStatus(""); setPage(1); }}>
                Voir toutes les commandes
              </button>
            ) : undefined
          }
        />
      )}

      {!isError && data && data.items.length > 0 && (
        <>
          <div className="flex flex-wrap items-center justify-between gap-2">
            <p className="text-sm text-madec-muted">
              <span className="font-semibold text-madec-text">{data.total}</span>
              {" "}commande{data.total > 1 ? "s" : ""}
              {status ? (
                <>
                  {" "}· <span className="text-madec-text">{orderStatusLabel(status)}</span>
                </>
              ) : null}
            </p>
            <p className="text-xs text-madec-muted">{ORDER_PAGE_SIZE} par page</p>
          </div>

          <div className="card !p-0 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="data-table !rounded-none !border-0 !shadow-none">
                <thead>
                  <tr>
                    <th>Référence</th>
                    {user?.role !== "acheteur" && <th>Client</th>}
                    <th>Statut</th>
                    <th>Paiement</th>
                    <th className="text-right">Montant à payer</th>
                    <th>Date</th>
                    <th className="w-10" />
                  </tr>
                </thead>
                <tbody>
                  {data.items.map((order) => (
                    <tr
                      key={order.id}
                      className="cursor-pointer"
                      onClick={() => setSelectedId(order.id)}
                    >
                      <td>
                        <span className="font-mono text-xs font-medium text-madec-text">{order.sorder_code}</span>
                      </td>
                      {user?.role !== "acheteur" && (
                        <td className="text-madec-secondary">
                          <p className="max-w-[12rem] truncate text-sm font-medium">
                            {order.user_name || order.user_email || `#${order.user_id}`}
                          </p>
                          {order.user_name && order.user_email && (
                            <p className="max-w-[12rem] truncate text-xs text-madec-muted">{order.user_email}</p>
                          )}
                        </td>
                      )}
                      <td><StatusBadge status={order.sorder_status} /></td>
                      <td className="text-madec-secondary">{paymentModeLabel(order.payment_mode)}</td>
                      <td className="text-right font-semibold text-madec-primary">
                        {formatMAD(Number(order.bl_amount != null ? order.bl_amount : order.dueamount))}
                      </td>
                      <td className="whitespace-nowrap text-madec-muted">
                        {format(new Date(order.created_at), "d MMM yyyy", { locale: fr })}
                      </td>
                      <td>
                        <button
                          type="button"
                          onClick={(e) => { e.stopPropagation(); setSelectedId(order.id); }}
                          className="rounded-lg p-1.5 text-madec-muted transition-colors hover:bg-madec-active hover:text-madec-primary"
                          title="Voir le détail"
                        >
                          <ChevronRight size={16} />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <Pagination
              page={data.page}
              pages={data.pages}
              total={data.total}
              pageSize={ORDER_PAGE_SIZE}
              onChange={setPage}
            />
          </div>
        </>
      )}

      <Modal open={selectedId !== null} onClose={closeOrderDetail} title="Détail commande" size="lg">
        {selectedId !== null && <OrderDetailPanel orderId={selectedId} onClose={closeOrderDetail} />}
      </Modal>

      <Modal open={cartOpen} onClose={() => setCartOpen(false)} title="Votre panier" size="md">
        <CartDrawer onClose={() => setCartOpen(false)} />
      </Modal>
    </div>
  );
}
