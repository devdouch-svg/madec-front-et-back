import { useQuery, useMutation } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import api from "../lib/api";
import { useAuth } from "../store/auth";
import toast from "react-hot-toast";
import { getErrorMessage } from "../lib/errors";
import { Spinner } from "../components/ui/Spinner";
import { PageLoader } from "../components/ui/Spinner";
import { ErrorState } from "../components/ui/ErrorState";
import type { PlafondStatus } from "../lib/types";
import { useRole } from "../lib/roles";
import { ROLE_LABELS } from "../lib/roles";
import { formatMAD, paymentModeLabel } from "../lib/labels";
import { PASSWORD_HINT, passwordField } from "../lib/password";
import { PageHeader } from "../components/layout/PageHeader";
import { RoleBadge } from "../components/ui/RoleBadge";

const LANGUE_OPTIONS = [
  { value: "fr", label: "Français" },
  { value: "ar", label: "العربية" },
] as const;

const profileSchema = z.object({
  first_name: z.string().optional(),
  last_name:  z.string().optional(),
  phone:      z.string().optional(),
  langue:     z.enum(["fr", "ar"]).optional(),
});

const pwSchema = z.object({
  current_password: z.string().min(1, "Requis"),
  new_password: passwordField,
});

type ProfileForm = z.infer<typeof profileSchema>;
type PwForm     = z.infer<typeof pwSchema>;

export function ProfilePage() {
  const { user, fetchMe } = useAuth();
  const { isAcheteur, role } = useRole();

  const {
    data: plafond,
    isLoading: plafondLoading,
    isError: plafondError,
    refetch: refetchPlafond,
  } = useQuery<PlafondStatus>({
    queryKey: ["my-plafond"],
    queryFn: () => api.get("/users/me/plafond").then((r) => r.data),
    enabled: isAcheteur,
  });

  const { register: rp, handleSubmit: hsp } = useForm<ProfileForm>({
    resolver: zodResolver(profileSchema),
    values: {
      first_name: user?.first_name ?? "",
      last_name:  user?.last_name  ?? "",
      phone:      user?.phone      ?? "",
      langue:     (user?.langue === "ar" ? "ar" : "fr"),
    },
  });

  const { register: rw, handleSubmit: hsw, formState: { errors: ew }, reset: resetPw } = useForm<PwForm>({
    resolver: zodResolver(pwSchema),
  });

  const updateProfile = useMutation({
    mutationFn: (d: ProfileForm) => api.put("/users/me", d),
    onSuccess: () => { toast.success("Profil mis à jour"); fetchMe(); },
    onError: (e) => toast.error(getErrorMessage(e, "Erreur")),
  });

  const changePw = useMutation({
    mutationFn: (d: PwForm) => api.post("/auth/change-password", d),
    onSuccess: () => { toast.success("Mot de passe changé"); resetPw(); },
    onError: (e) => toast.error(getErrorMessage(e, "Mot de passe incorrect")),
  });

  if (!user) return <PageLoader />;

  return (
    <div className="page-content max-w-2xl space-y-6">
      <PageHeader
        title="Mon profil"
        subtitle="Gérez vos informations et votre sécurité"
        actions={role ? <RoleBadge role={role} /> : undefined}
      />

      <div className="card">
        <h2 className="text-sm font-semibold text-madec-text mb-4">Informations personnelles</h2>
        <form onSubmit={hsp((d) => updateProfile.mutate(d))} className="space-y-3">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label" htmlFor="profile-first-name">Prénom</label>
              <input id="profile-first-name" {...rp("first_name")} className="input" />
            </div>
            <div>
              <label className="label" htmlFor="profile-last-name">Nom</label>
              <input id="profile-last-name" {...rp("last_name")} className="input" />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label" htmlFor="profile-phone">Téléphone</label>
              <input id="profile-phone" {...rp("phone")} className="input" />
            </div>
            <div>
              <label className="label" htmlFor="profile-langue">Langue</label>
              <select id="profile-langue" {...rp("langue")} className="input">
                {LANGUE_OPTIONS.map((o) => (
                  <option key={o.value} value={o.value}>{o.label}</option>
                ))}
              </select>
            </div>
          </div>
          <div>
            <label className="label" htmlFor="profile-email">Email (lecture seule)</label>
            <input id="profile-email" value={user.email ?? ""} disabled className="input" />
          </div>

          <div className="grid grid-cols-2 gap-3 text-sm">
            <div className="rounded-xl border border-madec-border bg-madec-surface px-3 py-2">
              <p className="text-xs text-madec-muted">Rôle</p>
              <p className="font-medium text-madec-text">{role ? ROLE_LABELS[role] : "—"}</p>
            </div>
            <div className="rounded-xl border border-madec-border bg-madec-surface px-3 py-2">
              <p className="text-xs text-madec-muted">Mode paiement</p>
              <p className="font-medium text-madec-text">{user.payment_mode ? paymentModeLabel(user.payment_mode) : "—"}</p>
            </div>
            {user.societe && (
              <div className="rounded-xl border border-madec-border bg-madec-surface px-3 py-2">
                <p className="text-xs text-madec-muted">Société</p>
                <p className="font-medium text-madec-text">{user.societe}</p>
              </div>
            )}
            {user.agence && (
              <div className="rounded-xl border border-madec-border bg-madec-surface px-3 py-2">
                <p className="text-xs text-madec-muted">Agence</p>
                <p className="font-medium text-madec-text">{user.agence}</p>
              </div>
            )}
          </div>

          {isAcheteur && plafondLoading && (
            <div className="flex justify-center py-4"><Spinner /></div>
          )}
          {isAcheteur && plafondError && (
            <ErrorState message="Impossible de charger le plafond mensuel." onRetry={() => refetchPlafond()} />
          )}
          {plafond && (
            <div className="rounded-xl border border-madec-tint bg-madec-active/50 px-4 py-3 text-sm">
              <p className="text-xs font-semibold uppercase tracking-wide text-madec-primary">Plafond mensuel</p>
              {plafond.plafond_mensuel == null ? (
                <p className="mt-1 font-medium text-madec-text">
                  Illimité — dépensé : {formatMAD(plafond.spent_this_month)}
                </p>
              ) : (
                <p className="mt-1 text-madec-text">
                  {formatMAD(plafond.spent_this_month)} / {formatMAD(plafond.plafond_mensuel)}
                  {plafond.remaining != null && (
                    <span className="text-madec-primary"> — reste {formatMAD(plafond.remaining)}</span>
                  )}
                </p>
              )}
            </div>
          )}

          <div className="flex justify-end">
            <button type="submit" disabled={updateProfile.isPending} className="btn-primary">
              {updateProfile.isPending ? <Spinner size="sm" /> : "Enregistrer"}
            </button>
          </div>
        </form>
      </div>

      <div className="card">
        <h2 className="text-sm font-semibold text-madec-text mb-4">Changer le mot de passe</h2>
        <form onSubmit={hsw((d) => changePw.mutate(d))} className="space-y-3">
          <div>
            <label className="label" htmlFor="pw-current">Mot de passe actuel</label>
            <input id="pw-current" {...rw("current_password")} type="password" className="input" autoComplete="current-password" />
            {ew.current_password && <p className="text-xs text-red-500 mt-0.5">{ew.current_password.message}</p>}
          </div>
          <div>
            <label className="label" htmlFor="pw-new">Nouveau mot de passe</label>
            <input id="pw-new" {...rw("new_password")} type="password" className="input" autoComplete="new-password" />
            <p className="mt-1.5 text-xs text-madec-muted">{PASSWORD_HINT}</p>
            {ew.new_password && <p className="text-xs text-red-500 mt-0.5">{ew.new_password.message}</p>}
          </div>
          <div className="flex justify-end">
            <button type="submit" disabled={changePw.isPending} className="btn-primary">
              {changePw.isPending ? <Spinner size="sm" /> : "Modifier"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
