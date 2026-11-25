import { useEffect, useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { RefreshCw, KeyRound, Copy, CheckCircle, Activity, Database } from "lucide-react";
import { syncApi } from "../lib/api/services";
import { PageHeader } from "../components/layout/PageHeader";
import { AdminOnlyBanner } from "../components/staff/AdminOnlyBanner";
import { RoleBadge } from "../components/ui/RoleBadge";
import { PageLoader } from "../components/ui/Spinner";
import { Pagination } from "../components/ui/Pagination";
import { StatusBadge } from "../components/ui/StatusBadge";
import toast from "react-hot-toast";
import { format } from "date-fns";
import { fr } from "date-fns/locale";

export function SyncPage() {
  const qc = useQueryClient();
  const [page, setPage] = useState(1);
  const [entityFilter, setEntityFilter] = useState("");
  const [rotatedToken, setRotatedToken] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (!rotatedToken) return;
    const timer = window.setTimeout(() => setRotatedToken(null), 120_000);
    return () => {
      window.clearTimeout(timer);
      setRotatedToken(null);
    };
  }, [rotatedToken]);

  const { data: overview, isLoading: overviewLoading } = useQuery({
    queryKey: ["sync-overview"],
    queryFn: () => syncApi.overview().then((r) => r.data),
  });

  const { data: logs, isLoading: logsLoading } = useQuery({
    queryKey: ["sync-logs", page, entityFilter],
    queryFn: () => syncApi.logs(page, entityFilter || undefined).then((r) => r.data),
  });

  const rotate = useMutation({
    mutationFn: () => syncApi.rotateToken().then((r) => r.data),
    onSuccess: (data) => {
      setRotatedToken(data.token);
      toast.success("Token ETL rotaté");
      qc.invalidateQueries({ queryKey: ["sync-overview"] });
    },
    onError: (e: any) => toast.error(e?.response?.data?.detail ?? "Erreur"),
  });

  const copyToken = () => {
    if (rotatedToken) {
      navigator.clipboard.writeText(rotatedToken);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  if (overviewLoading && !overview) return <PageLoader />;

  return (
    <div className="page-content max-w-6xl space-y-6">
      <PageHeader
        title="Synchronisation ETL"
        subtitle="Historique des syncs, état du système et rotation du token de service"
        actions={<RoleBadge role="admin" />}
      />

      <AdminOnlyBanner page="sync" />

      <div className="grid gap-4 sm:grid-cols-3">
        <div className="card flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-madec-active text-madec-primary">
            <Database size={20} />
          </div>
          <div>
            <p className="text-xs text-madec-muted">Base de données</p>
            <p className="font-semibold text-madec-text capitalize">{overview?.db ?? "—"}</p>
          </div>
        </div>
        <div className="card flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-madec-active text-madec-primary">
            <Activity size={20} />
          </div>
          <div>
            <p className="text-xs text-madec-muted">Version API</p>
            <p className="font-semibold text-madec-text">{overview?.app_version ?? "—"}</p>
          </div>
        </div>
        <div className="card">
          <p className="text-xs font-semibold uppercase tracking-wide text-madec-muted mb-2">Dernière sync</p>
          <div className="space-y-1 text-xs">
            {["products", "users", "orders"].map((key) => {
              const row = overview?.last_sync?.[key];
              return (
                <div key={key} className="flex justify-between gap-2">
                  <span className="capitalize text-madec-secondary">{key}</span>
                  {row ? (
                    <span className="text-madec-text">
                      <StatusBadge status={row.status === "success" ? "active" : row.status === "error" ? "cancelled" : "pending"} />
                    </span>
                  ) : (
                    <span className="text-madec-muted">—</span>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </div>

      <div className="card">
        <h2 className="text-sm font-semibold text-madec-text mb-3">Rotation du token de service</h2>
        <p className="text-sm text-madec-muted mb-4">
          Génère un nouveau token ETL et désactive les anciens. Le token n&apos;est affiché qu&apos;une seule fois.
        </p>
        <button
          onClick={() => rotate.mutate()}
          disabled={rotate.isPending}
          className="btn-primary btn-sm"
        >
          <KeyRound size={14} /> {rotate.isPending ? "Rotation..." : "Rotater le token ETL"}
        </button>

        {rotatedToken && (
          <div className="mt-4 rounded-xl border border-amber-200 bg-amber-50 p-4">
            <p className="text-sm font-semibold text-amber-900 mb-2">Copiez ce token maintenant</p>
            <div className="flex items-center gap-2">
              <code className="flex-1 break-all rounded-lg border bg-white px-3 py-2 font-mono text-xs">
                {rotatedToken}
              </code>
              <button onClick={copyToken} className="btn-secondary btn-sm shrink-0">
                {copied ? <CheckCircle size={14} className="text-green-600" /> : <Copy size={14} />}
              </button>
            </div>
          </div>
        )}
      </div>

      <div className="card border-madec-tint bg-madec-active/50">
        <p className="text-sm font-semibold text-primary-900 mb-2">Endpoints ETL (token de service requis)</p>
        <p className="text-xs text-madec-primary mb-2">
          Ces routes sont appelées par l&apos;intégration ETL, pas par l&apos;interface web.
        </p>
        <ul className="space-y-1 font-mono text-xs text-madec-primary">
          <li>GET  /api/v1/sync/health</li>
          <li>POST /api/v1/sync/products/bulk</li>
          <li>POST /api/v1/sync/users/bulk</li>
          <li>POST /api/v1/sync/orders/push</li>
          <li>PATCH /api/v1/sync/orders/{"{id}"}/status</li>
          <li>PATCH /api/v1/sync/orders/{"{id}"}/bl</li>
          <li>PATCH /api/v1/sync/orders/{"{id}"}/flag</li>
        </ul>
      </div>

      <div className="card !p-0 overflow-hidden">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b px-4 py-3">
          <h2 className="text-sm font-semibold text-madec-text flex items-center gap-2">
            <RefreshCw size={16} /> Journal des synchronisations
          </h2>
          <select
            className="input w-40 py-1.5 text-sm"
            value={entityFilter}
            onChange={(e) => { setEntityFilter(e.target.value); setPage(1); }}
          >
            <option value="">Toutes les entités</option>
            <option value="products">Produits</option>
            <option value="users">Utilisateurs</option>
            <option value="orders">Commandes</option>
          </select>
        </div>

        {logsLoading && !logs ? (
          <div className="p-8"><PageLoader /></div>
        ) : (
          <>
            <table className="data-table w-full">
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Entité</th>
                  <th>Opération</th>
                  <th>Statut</th>
                  <th className="text-right">OK</th>
                  <th className="text-right">Échecs</th>
                </tr>
              </thead>
              <tbody>
                {logs?.items.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="py-8 text-center text-madec-muted">
                      Aucune synchronisation enregistrée
                    </td>
                  </tr>
                ) : (
                  logs?.items.map((log) => (
                    <tr key={log.id}>
                      <td className="text-xs text-madec-muted">
                        {format(new Date(log.started_at), "d MMM yyyy HH:mm", { locale: fr })}
                      </td>
                      <td className="capitalize">{log.entity_type}</td>
                      <td>{log.operation}</td>
                      <td>
                        <StatusBadge
                          status={
                            log.status === "success" ? "active" : log.status === "error" ? "cancelled" : "pending"
                          }
                        />
                      </td>
                      <td className="text-right">{log.records_processed}</td>
                      <td className="text-right text-red-600">{log.records_failed}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
            {logs && logs.pages > 1 && (
              <Pagination
                page={logs.page}
                pages={logs.pages}
                total={logs.total}
                pageSize={logs.page_size}
                onChange={setPage}
              />
            )}
          </>
        )}
      </div>
    </div>
  );
}
