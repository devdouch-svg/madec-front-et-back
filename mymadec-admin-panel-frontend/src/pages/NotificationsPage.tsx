import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Bell, CheckCheck, Trash2, Send } from "lucide-react";
import api from "../lib/api";
import { getErrorMessage } from "../lib/errors";
import type { Notification, PaginatedResponse, User } from "../lib/types";
import { PageLoader } from "../components/ui/Spinner";
import { Pagination } from "../components/ui/Pagination";
import { Modal } from "../components/ui/Modal";
import { ConfirmModal } from "../components/ui/ConfirmModal";
import { useRole } from "../lib/roles";
import { staffCan } from "../lib/staffCapabilities";
import { useUnreadCount } from "../hooks/useUnreadCount";
import { AdminOnlyBanner } from "../components/staff/AdminOnlyBanner";
import toast from "react-hot-toast";
import { format } from "date-fns";
import { fr } from "date-fns/locale";

function SendNotificationModal({ open, onClose }: { open: boolean; onClose: () => void }) {
  const qc = useQueryClient();
  const [userId, setUserId] = useState("");
  const [title, setTitle] = useState("");
  const [body, setBody] = useState("");
  const [type, setType] = useState("general");

  const { data: users, isLoading: usersLoading } = useQuery<PaginatedResponse<User>>({
    queryKey: ["users-notif"],
    queryFn: () => api.get("/users?page_size=100&role=acheteur").then((r) => r.data),
    enabled: open,
  });

  const send = useMutation({
    mutationFn: () =>
      api.post("/notifications/send", { user_id: parseInt(userId), title, body, type }),
    onSuccess: () => {
      toast.success("Notification envoyée");
      setUserId(""); setTitle(""); setBody("");
      qc.invalidateQueries({ queryKey: ["notifications"] });
      onClose();
    },
    onError: (e) => toast.error(getErrorMessage(e, "Erreur lors de l'envoi")),
  });

  return (
    <Modal open={open} onClose={onClose} title="Envoyer une notification">
      <div className="space-y-3">
        <div>
          <label className="label" htmlFor="notif-user">Destinataire</label>
          {usersLoading ? (
            <p className="text-sm text-madec-muted">Chargement des utilisateurs…</p>
          ) : (
          <select id="notif-user" className="input" value={userId} onChange={(e) => setUserId(e.target.value)}>
            <option value="">Sélectionner...</option>
            {users?.items.map((u) => (
              <option key={u.id} value={u.id}>
                {u.first_name} {u.last_name} ({u.email})
              </option>
            ))}
          </select>
          )}
        </div>
        <div>
          <label className="label" htmlFor="notif-title">Titre</label>
          <input id="notif-title" className="input" maxLength={200} value={title} onChange={(e) => setTitle(e.target.value)} />
        </div>
        <div>
          <label className="label" htmlFor="notif-type">Type</label>
          <select id="notif-type" className="input" value={type} onChange={(e) => setType(e.target.value)}>
            <option value="general">Général</option>
            <option value="order_status">Commande</option>
            <option value="promo">Promotion</option>
          </select>
        </div>
        <div>
          <label className="label" htmlFor="notif-body">Message</label>
          <textarea id="notif-body" className="input" rows={3} maxLength={2000} value={body} onChange={(e) => setBody(e.target.value)} />
        </div>
        <div className="flex justify-end gap-2">
          <button type="button" onClick={onClose} className="btn-secondary">Annuler</button>
          <button
            type="button"
            onClick={() => send.mutate()}
            disabled={!userId || !title.trim() || !body.trim() || send.isPending}
            className="btn-primary"
          >
            {send.isPending ? "Envoi..." : "Envoyer"}
          </button>
        </div>
      </div>
    </Modal>
  );
}

export function NotificationsPage() {
  const qc = useQueryClient();
  const { role } = useRole();
  const canSend = staffCan("send_notifications", role);
  const { data: unreadData } = useUnreadCount();
  const [sendOpen, setSendOpen] = useState(false);
  const [page, setPage] = useState(1);
  const [confirmDelete, setConfirmDelete] = useState<Notification | null>(null);

  const { data, isLoading } = useQuery<PaginatedResponse<Notification>>({
    queryKey: ["notifications", page],
    queryFn: () => api.get(`/notifications?page=${page}`).then((r) => r.data),
  });

  const markRead = useMutation({
    mutationFn: (id: number) => api.patch(`/notifications/${id}/read`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["notifications"] });
      qc.invalidateQueries({ queryKey: ["unread-count"] });
    },
    onError: (e) => toast.error(getErrorMessage(e, "Erreur")),
  });

  const markAll = useMutation({
    mutationFn: () => api.patch("/notifications/read-all"),
    onSuccess: () => {
      toast.success("Tout marqué comme lu");
      qc.invalidateQueries({ queryKey: ["notifications"] });
      qc.invalidateQueries({ queryKey: ["unread-count"] });
    },
    onError: (e) => toast.error(getErrorMessage(e, "Erreur")),
  });

  const del = useMutation({
    mutationFn: (id: number) => api.delete(`/notifications/${id}`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["notifications"] });
      qc.invalidateQueries({ queryKey: ["unread-count"] });
    },
    onError: (e) => toast.error(getErrorMessage(e, "Erreur")),
  });

  if (isLoading) return <PageLoader />;

  const items = data?.items ?? [];
  const unreadTotal = unreadData?.unread_count ?? 0;

  return (
    <div className="page-content w-full max-w-full space-y-4">
      <div className="flex items-center gap-3">
        <h1 className="page-title flex-1">
          Notifications{unreadTotal > 0 && (
            <span className="ml-2 badge bg-red-100 text-red-700">{unreadTotal}</span>
          )}
        </h1>
        {unreadTotal > 0 && (
          <button type="button" onClick={() => markAll.mutate()} className="btn-secondary btn-sm" disabled={markAll.isPending}>
            <CheckCheck size={14} /> Tout lire
          </button>
        )}
        {canSend && (
          <button type="button" onClick={() => setSendOpen(true)} className="btn-primary btn-sm">
            <Send size={14} /> Envoyer
          </button>
        )}
      </div>

      {canSend && <AdminOnlyBanner page="notifications" />}

      {items.length === 0 ? (
        <div className="text-center py-16 text-madec-muted">
          <Bell size={40} className="mx-auto mb-3 opacity-30" />
          <p>Aucune notification</p>
        </div>
      ) : (
        <div className="space-y-2">
          {items.map((n) => (
            <div
              key={n.id}
              className={`flex gap-3 rounded-xl border p-4 transition-colors ${
                n.is_read ? "border-madec-border bg-white" : "border-madec-tint bg-madec-active"
              }`}
            >
              <div className={`mt-0.5 h-2 w-2 shrink-0 rounded-full ${n.is_read ? "bg-madec-border" : "bg-madec-primary"}`} />
              <div className="flex-1 min-w-0">
                <p className="text-sm font-semibold text-madec-text">{n.title}</p>
                <p className="text-sm text-madec-secondary mt-0.5">{n.body}</p>
                <p className="text-xs text-madec-muted mt-1">
                  {format(new Date(n.created_at), "d MMM yyyy à HH:mm", { locale: fr })}
                </p>
              </div>
              <div className="flex shrink-0 items-start gap-2">
                {!n.is_read && (
                  <button
                    type="button"
                    onClick={() => markRead.mutate(n.id)}
                    className="text-madec-muted hover:text-madec-primary"
                    aria-label="Marquer comme lue"
                  >
                    <CheckCheck size={15} />
                  </button>
                )}
                <button
                  type="button"
                  onClick={() => setConfirmDelete(n)}
                  className="text-madec-muted/50 hover:text-red-500"
                  aria-label="Supprimer la notification"
                >
                  <Trash2 size={14} />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {data && data.pages > 1 && (
        <Pagination
          page={data.page} pages={data.pages}
          total={data.total} pageSize={data.page_size}
          onChange={setPage}
        />
      )}

      <SendNotificationModal open={sendOpen} onClose={() => setSendOpen(false)} />

      <ConfirmModal
        open={!!confirmDelete}
        title="Supprimer la notification"
        message="Cette notification sera définitivement supprimée."
        confirmLabel="Supprimer"
        danger
        onConfirm={() => confirmDelete && del.mutate(confirmDelete.id)}
        onClose={() => setConfirmDelete(null)}
      />
    </div>
  );
}
