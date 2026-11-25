import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import api from "../lib/api";
import { getErrorMessage } from "../lib/errors";
import type { PaginatedResponse, User } from "../lib/types";
import {
  ATOMIC_PAYMENT_MODES,
  PAYMENT_LABELS,
  expandPaymentModes,
  paymentModeLabel,
} from "../lib/labels";
import toast from "react-hot-toast";
import { CreditCard, Banknote, Search, Landmark } from "lucide-react";
import { PageHeader } from "../components/layout/PageHeader";
import { PageLoader } from "../components/ui/Spinner";
import { ErrorState } from "../components/ui/ErrorState";
import { useAuth } from "../store/auth";
import { useRole } from "../lib/roles";
import { staffCan } from "../lib/staffCapabilities";
import { AdminOnlyBanner } from "../components/staff/AdminOnlyBanner";

const MODE_ICONS: Record<string, React.ReactNode> = {
  especes: <Banknote size={22} />,
  carte: <CreditCard size={22} />,
  deduction_salaire: <Landmark size={22} />,
};

export function PaymentMethodsPage() {
  const { user } = useAuth();
  const { role } = useRole();
  const qc = useQueryClient();
  const canManage = staffCan("payment_methods_admin", role);
  const [search, setSearch] = useState("");

  const { data: myModes, isLoading: modesLoading, isError: modesError, refetch } = useQuery<string[]>({
    queryKey: ["payment-modes-me"],
    queryFn: () => api.get("/payment-methods").then((r) => r.data),
  });

  const { data: users, isLoading: usersLoading, isError: usersError } = useQuery<PaginatedResponse<User>>({
    queryKey: ["users-payment", search],
    queryFn: () =>
      api
        .get(`/users?page_size=100&role=acheteur${search ? `&search=${encodeURIComponent(search)}` : ""}`)
        .then((r) => r.data),
    enabled: canManage,
  });

  const setModes = useMutation({
    mutationFn: ({ userId, modes }: { userId: number; modes: string[] }) =>
      api.put(`/payment-methods/${userId}/modes`, { modes }),
    onSuccess: () => {
      toast.success("Modes de paiement mis à jour");
      qc.invalidateQueries({ queryKey: ["users-payment"] });
      qc.invalidateQueries({ queryKey: ["users"] });
    },
    onError: (e) => toast.error(getErrorMessage(e, "Erreur")),
  });

  const toggleMode = (u: User, mode: string) => {
    const current = expandPaymentModes(u.payment_mode);
    const next = current.includes(mode)
      ? current.filter((m) => m !== mode)
      : [...current, mode];
    if (next.length === 0) {
      toast.error("Au moins un mode est requis");
      return;
    }
    setModes.mutate({ userId: u.id, modes: next });
  };

  const displayModes = myModes ?? expandPaymentModes(user?.payment_mode);

  if (modesLoading) return <PageLoader />;

  return (
    <div className="page-content w-full max-w-full space-y-6">
      <PageHeader
        title="Mode de paiement"
        subtitle={
          canManage
            ? "Cochez Espèces / Carte / Déduction pour chaque acheteur"
            : "Vos modes de paiement assignés par l'administrateur"
        }
      />

      {canManage && <AdminOnlyBanner page="payment" />}

      {modesError && <ErrorState onRetry={() => refetch()} />}

      <div className="card space-y-4">
        <h2 className="text-sm font-semibold text-madec-text">Vos modes actuels</h2>
        <div className="flex flex-wrap gap-2">
          {displayModes.map((m) => (
            <span
              key={m}
              className="flex items-center gap-1.5 rounded-lg border-2 border-madec-tint bg-madec-active px-3 py-2 text-sm font-medium text-madec-primary"
            >
              {MODE_ICONS[m]}
              {PAYMENT_LABELS[m] ?? m}
            </span>
          ))}
        </div>
        {displayModes.length > 1 && (
          <p className="text-xs text-madec-muted">
            Plusieurs modes : vous choisissez à chaque commande.
          </p>
        )}
        {!canManage && (
          <p className="text-xs text-madec-muted">
            Pour modifier vos modes, contactez votre administrateur.
          </p>
        )}
      </div>

      {canManage && (
        <div className="card">
          <h2 className="mb-1 text-sm font-semibold text-madec-text">
            Gérer le paiement des utilisateurs
          </h2>
          <p className="mb-3 text-xs text-madec-muted">
            Cochez une ou plusieurs options par personne (Espèces, Carte, Déduction).
          </p>
          <div className="relative mb-3 max-w-sm">
            <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-madec-muted" />
            <input
              className="input pl-9"
              placeholder="Rechercher un acheteur…"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
          {usersLoading && <PageLoader />}
          {usersError && (
            <ErrorState onRetry={() => qc.invalidateQueries({ queryKey: ["users-payment"] })} />
          )}
          {users && (
            <div className="max-h-96 space-y-2 overflow-y-auto">
              {users.items.length === 0 ? (
                <p className="text-sm text-madec-muted">Aucun utilisateur trouvé.</p>
              ) : (
                users.items.map((u) => {
                  const active = expandPaymentModes(u.payment_mode);
                  return (
                    <div
                      key={u.id}
                      className="flex flex-col gap-2 rounded-lg bg-madec-surface px-3 py-2 text-sm sm:flex-row sm:items-center sm:justify-between"
                    >
                      <div className="min-w-0">
                        <p className="font-medium text-madec-text">
                          {u.first_name} {u.last_name}
                        </p>
                        <p className="truncate text-xs text-madec-muted">{u.email}</p>
                        <p className="mt-0.5 text-xs text-madec-primary">
                          {paymentModeLabel(u.payment_mode)}
                        </p>
                      </div>
                      <div className="flex flex-wrap gap-2">
                        {ATOMIC_PAYMENT_MODES.map((mode) => {
                          const on = active.includes(mode);
                          return (
                            <label
                              key={mode}
                              className={`inline-flex cursor-pointer items-center gap-1.5 rounded border px-2 py-1 text-xs transition-colors ${
                                on
                                  ? "border-madec-primary bg-madec-primary text-white"
                                  : "border-madec-border bg-white hover:border-madec-primary"
                              } ${setModes.isPending ? "opacity-60" : ""}`}
                            >
                              <input
                                type="checkbox"
                                className="sr-only"
                                checked={on}
                                disabled={setModes.isPending}
                                onChange={() => toggleMode(u, mode)}
                              />
                              {MODE_ICONS[mode]}
                              {mode === "deduction_salaire" ? "Déduction" : PAYMENT_LABELS[mode]}
                            </label>
                          );
                        })}
                        <button
                          type="button"
                          title="Activer tous les modes (espèces, carte, déduction)"
                          disabled={setModes.isPending || active.length === ATOMIC_PAYMENT_MODES.length}
                          onClick={() =>
                            setModes.mutate({
                              userId: u.id,
                              modes: [...ATOMIC_PAYMENT_MODES],
                            })
                          }
                          className={`rounded border px-2 py-1 text-xs font-semibold transition-colors ${
                            active.length === ATOMIC_PAYMENT_MODES.length
                              ? "cursor-default border-madec-primary bg-madec-tint text-madec-primary"
                              : "border-madec-border bg-white hover:border-madec-primary hover:bg-madec-active"
                          }`}
                        >
                          Tous
                        </button>
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
