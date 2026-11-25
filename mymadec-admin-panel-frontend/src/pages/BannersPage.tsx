import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { ToggleLeft, ToggleRight, Upload } from "lucide-react";
import api from "../lib/api";
import { getErrorMessage } from "../lib/errors";
import type { Banner } from "../lib/types";
import { PageLoader } from "../components/ui/Spinner";
import toast from "react-hot-toast";
import { useRef } from "react";

import { mediaUrl } from "../lib/media";
import { PageHeader } from "../components/layout/PageHeader";
import { AdminOnlyBanner } from "../components/staff/AdminOnlyBanner";
import { RoleBadge } from "../components/ui/RoleBadge";

export function BannersPage() {
  const qc = useQueryClient();
  const fileRefs = useRef<Record<number, HTMLInputElement | null>>({});

  const { data, isLoading } = useQuery<Banner[]>({
    queryKey: ["banners-all"],
    queryFn: () => api.get("/banners?include_inactive=true").then((r) => r.data),
  });

  const toggle = useMutation({
    mutationFn: (id: number) => api.patch(`/banners/${id}/toggle`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["banners-all"] }),
  });

  const upload = useMutation({
    mutationFn: ({ id, file }: { id: number; file: File }) => {
      const fd = new FormData(); fd.append("file", file);
      return api.post(`/banners/${id}/image`, fd);
    },
    onSuccess: () => { toast.success("Image mise à jour"); qc.invalidateQueries({ queryKey: ["banners-all"] }); },
    onError: (e) => toast.error(getErrorMessage(e, "Erreur upload")),
  });

  const update = useMutation({
    mutationFn: ({ id, ...body }: { id: number; title?: string; subtitle?: string; link_url?: string }) =>
      api.put(`/banners/${id}`, body),
    onSuccess: () => { toast.success("Bannière mise à jour"); qc.invalidateQueries({ queryKey: ["banners-all"] }); },
  });

  if (isLoading) return <PageLoader />;

  return (
    <div className="page-content max-w-7xl space-y-4">
      <PageHeader
        title="Bannières"
        subtitle="Images et liens affichés sur l'accueil mobile"
        actions={<RoleBadge role="admin" />}
      />
      <AdminOnlyBanner page="banners" />
      <div className="space-y-4">
        {data?.map((b) => (
          <div key={b.id} className="card flex gap-6 items-start">
            {/* Image */}
            <div className="relative shrink-0">
              {b.image_path ? (
                <img src={mediaUrl(b.image_path, b.updated_at)} alt="" className="h-32 w-56 object-cover rounded-lg" />
              ) : (
                <div className="h-32 w-56 bg-madec-tint rounded-lg flex items-center justify-center text-madec-muted/50 text-4xl">🖼</div>
              )}
              <button
                onClick={() => fileRefs.current[b.id]?.click()}
                className="absolute bottom-2 right-2 btn-secondary btn-sm !p-1.5"
              >
                <Upload size={13} />
              </button>
              <input
                type="file" accept="image/*" className="hidden"
                ref={(el) => { fileRefs.current[b.id] = el; }}
                onChange={(e) => { const f = e.target.files?.[0]; if (f) upload.mutate({ id: b.id, file: f }); }}
              />
            </div>

            {/* Fields */}
            <div className="flex-1 space-y-3">
              <div className="flex items-center gap-3">
                <span className="badge bg-madec-tint text-madec-secondary">Position {b.position}</span>
                <button onClick={() => toggle.mutate(b.id)} className="flex items-center gap-1 text-sm text-madec-muted hover:text-madec-primary">
                  {b.is_active ? <ToggleRight size={18} className="text-green-500" /> : <ToggleLeft size={18} />}
                  {b.is_active ? "Active" : "Inactive"}
                </button>
              </div>
              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="label">Titre</label>
                  <input
                    defaultValue={b.title ?? ""}
                    onBlur={(e) => update.mutate({ id: b.id, title: e.target.value })}
                    className="input"
                  />
                </div>
                <div>
                  <label className="label">Sous-titre</label>
                  <input
                    defaultValue={b.subtitle ?? ""}
                    onBlur={(e) => update.mutate({ id: b.id, subtitle: e.target.value })}
                    className="input"
                  />
                </div>
                <div>
                  <label className="label">Lien URL</label>
                  <input
                    defaultValue={b.link_url ?? ""}
                    onBlur={(e) => update.mutate({ id: b.id, link_url: e.target.value })}
                    className="input"
                  />
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
