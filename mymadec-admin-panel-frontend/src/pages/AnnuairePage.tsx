import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Search, Mail, Phone } from "lucide-react";
import api from "../lib/api";
import type { AnnuaireEntry, PaginatedResponse } from "../lib/types";
import { PageLoader } from "../components/ui/Spinner";
import { Pagination } from "../components/ui/Pagination";
import { Modal } from "../components/ui/Modal";
import { PageHeader } from "../components/layout/PageHeader";
import { AdminOnlyBanner } from "../components/staff/AdminOnlyBanner";
import { RoleBadge } from "../components/ui/RoleBadge";

function EntryDetail({ entry }: { entry: AnnuaireEntry }) {
  return (
    <div className="space-y-3 text-sm">
      <div>
        <p className="text-madec-muted">Nom complet</p>
        <p className="font-medium">{entry.first_name} {entry.last_name}</p>
      </div>
      <div className="flex items-center gap-2">
        <Mail size={14} className="text-madec-muted" />
        <a href={`mailto:${entry.email}`} className="text-madec-primary hover:underline">{entry.email}</a>
      </div>
      {entry.phone && (
        <div className="flex items-center gap-2">
          <Phone size={14} className="text-madec-muted" />
          <a href={`tel:${entry.phone}`} className="text-madec-primary hover:underline">{entry.phone}</a>
        </div>
      )}
      <div>
        <p className="text-madec-muted">Rôle</p>
        <span className="badge bg-madec-tint text-madec-text">{entry.role}</span>
      </div>
      {entry.societe && (
        <div>
          <p className="text-madec-muted">Société</p>
          <p className="font-medium">{entry.societe}</p>
        </div>
      )}
      {entry.agence && (
        <div>
          <p className="text-madec-muted">Agence</p>
          <p className="font-medium">{entry.agence}</p>
        </div>
      )}
      {entry.matricule && (
        <div>
          <p className="text-madec-muted">Matricule</p>
          <p className="font-mono font-medium">{entry.matricule}</p>
        </div>
      )}
    </div>
  );
}

export function AnnuairePage() {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [selectedId, setSelectedId] = useState<number | null>(null);

  const { data, isLoading } = useQuery<PaginatedResponse<AnnuaireEntry>>({
    queryKey: ["annuaire-list", page, search],
    queryFn: () =>
      api.get(`/annuaire?page=${page}${search ? `&search=${encodeURIComponent(search)}` : ""}`).then((r) => r.data),
  });

  const { data: selected, isLoading: detailLoading } = useQuery<AnnuaireEntry>({
    queryKey: ["annuaire-detail", selectedId],
    queryFn: () => api.get(`/annuaire/${selectedId}`).then((r) => r.data),
    enabled: selectedId != null,
  });

  if (isLoading && !data) return <PageLoader />;

  return (
    <div className="page-content max-w-7xl space-y-4">
      <PageHeader
        title="Annuaire"
        subtitle="Répertoire des utilisateurs actifs de l'organisation"
        actions={<RoleBadge role="admin" />}
      />
      <AdminOnlyBanner page="annuaire" />

      <div className="relative max-w-md">
        <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-madec-muted" />
        <input
          className="input pl-9"
          placeholder="Rechercher par nom ou email..."
          value={search}
          onChange={(e) => { setSearch(e.target.value); setPage(1); }}
        />
      </div>

      <div className="card !p-0 overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-madec-surface text-xs text-madec-muted border-b">
            <tr>
              <th className="text-left px-4 py-3">Nom</th>
              <th className="text-left px-4 py-3">Email</th>
              <th className="text-left px-4 py-3">Téléphone</th>
              <th className="text-left px-4 py-3">Société</th>
              <th className="text-left px-4 py-3">Agence</th>
              <th className="text-left px-4 py-3">Rôle</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-madec-border">
            {data?.items.map((e) => (
              <tr key={e.id} className="hover:bg-madec-surface cursor-pointer" onClick={() => setSelectedId(e.id)}>
                <td className="px-4 py-3 font-medium">{e.first_name} {e.last_name}</td>
                <td className="px-4 py-3 text-madec-secondary">{e.email}</td>
                <td className="px-4 py-3 text-madec-secondary">{e.phone ?? "—"}</td>
                <td className="px-4 py-3 text-madec-secondary">{e.societe ?? "—"}</td>
                <td className="px-4 py-3 text-madec-secondary">{e.agence ?? "—"}</td>
                <td className="px-4 py-3"><span className="badge bg-madec-tint text-madec-text">{e.role}</span></td>
              </tr>
            ))}
          </tbody>
        </table>
        {data && (
          <Pagination page={data.page} pages={data.pages} total={data.total} pageSize={data.page_size} onChange={setPage} />
        )}
      </div>

      <Modal open={selectedId != null} onClose={() => setSelectedId(null)} title="Contact">
        {detailLoading ? <PageLoader /> : selected ? <EntryDetail entry={selected} /> : null}
      </Modal>
    </div>
  );
}
