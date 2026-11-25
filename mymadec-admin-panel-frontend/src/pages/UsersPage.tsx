import { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Search, ToggleLeft, ToggleRight, KeyRound, Plus, Pencil, Eye } from "lucide-react";
import api from "../lib/api";
import { getErrorMessage } from "../lib/errors";
import { ATOMIC_PAYMENT_MODES, PAYMENT_LABELS, expandPaymentModes, paymentModeLabel } from "../lib/labels";
import type { Order, PaginatedResponse, PlafondStatus, User } from "../lib/types";
import { PageLoader } from "../components/ui/Spinner";
import { StatusBadge } from "../components/ui/StatusBadge";
import { Pagination } from "../components/ui/Pagination";
import { Modal } from "../components/ui/Modal";
import { ConfirmModal } from "../components/ui/ConfirmModal";
import { useAuth } from "../store/auth";
import { useRole } from "../lib/roles";
import { StaffScopeBanner } from "../components/staff/StaffScopeBanner";
import { PageHeader } from "../components/layout/PageHeader";
import { useForm, Controller, useWatch, type Control, type UseFormSetValue } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import toast from "react-hot-toast";
import { ComboSelect } from "../components/ui/ComboSelect";
import {
  findSocieteId,
  useCatalogAgences,
  useCatalogSocietes,
  useCatalogVilles,
} from "../hooks/useCatalog";
import { format } from "date-fns";
import { fr } from "date-fns/locale";

const ROLES = ["admin", "gestionnaire", "acheteur", "service"] as const;
const PAYMENT_MODES = ["especes", "carte", "les_deux", "deduction_salaire"] as const;
const USER_PAGE_SIZE = 15;


const createSchema = z.object({
  email: z.string().email("Email invalide"),
  first_name: z.string().min(1, "Prénom requis"),
  last_name: z.string().optional(),
  phone: z.string().optional(),
  matricule: z.string().optional(),
  role: z.enum(ROLES),
  payment_mode: z.enum(PAYMENT_MODES),
  plafond_mensuel: z.number().nullable().optional(),
  societe: z.string().optional(),
  agence: z.string().optional(),
  ville: z.string().optional(),
  langue: z.string().optional(),
});
type CreateForm = z.infer<typeof createSchema>;

const editSchema = z.object({
  first_name: z.string().optional(),
  last_name: z.string().optional(),
  phone: z.string().optional(),
  matricule: z.string().optional(),
  productsalesgroup_code: z.string().optional(),
  societe: z.string().optional(),
  agence: z.string().optional(),
  ville: z.string().optional(),
});
type EditForm = z.infer<typeof editSchema>;

type OrgFormFields = { societe?: string; agence?: string; ville?: string };

function OrgFields({
  control,
  setValue,
  idPrefix,
}: {
  control: Control<OrgFormFields>;
  setValue: UseFormSetValue<OrgFormFields>;
  idPrefix: string;
}) {
  const societeVal = useWatch({ control, name: "societe" }) ?? "";
  const { data: societes } = useCatalogSocietes();
  const societeId = findSocieteId(societes, societeVal);
  const { data: agences } = useCatalogAgences(societeId);
  const { data: villes } = useCatalogVilles();

  return (
    <div className="grid grid-cols-3 gap-3">
      <div>
        <label className="label">Société</label>
        <Controller
          name="societe"
          control={control}
          render={({ field }) => (
            <ComboSelect
              id={`${idPrefix}-societe`}
              value={field.value ?? ""}
              onChange={(v) => { field.onChange(v); setValue("agence", ""); }}
              options={societes?.map((s) => s.code) ?? []}
              placeholder="Ex: MADEC"
            />
          )}
        />
      </div>
      <div>
        <label className="label">Agence</label>
        <Controller
          name="agence"
          control={control}
          render={({ field }) => (
            <ComboSelect
              id={`${idPrefix}-agence`}
              value={field.value ?? ""}
              onChange={field.onChange}
              options={agences?.map((a) => a.code) ?? []}
              placeholder="001"
            />
          )}
        />
      </div>
      <div>
        <label className="label">Ville</label>
        <Controller
          name="ville"
          control={control}
          render={({ field }) => (
            <ComboSelect
              id={`${idPrefix}-ville`}
              value={field.value ?? ""}
              onChange={field.onChange}
              options={villes?.map((v) => v.label) ?? []}
              placeholder="Ville"
            />
          )}
        />
      </div>
    </div>
  );
}

function CreateUserModal({ open, onClose }: { open: boolean; onClose: () => void }) {
  const qc = useQueryClient();
  const { register, handleSubmit, control, setValue, formState: { errors }, reset } = useForm<CreateForm>({
    resolver: zodResolver(createSchema),
    defaultValues: { role: "acheteur", payment_mode: "especes", langue: "fr" },
  });
  const create = useMutation({
    mutationFn: (d: CreateForm) => api.post("/users", d),
    onSuccess: () => { toast.success("Utilisateur créé — identifiants envoyés par email"); reset(); qc.invalidateQueries({ queryKey: ["users"] }); onClose(); },
    onError: (e) => toast.error(getErrorMessage(e, "Erreur lors de la création")),
  });
  return (
    <Modal open={open} onClose={onClose} title="Nouvel utilisateur">
      <form onSubmit={handleSubmit((d) => create.mutate(d))} className="space-y-3">
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="label">Prénom *</label>
            <input {...register("first_name")} className="input" />
            {errors.first_name && <p className="text-xs text-red-500 mt-0.5">{errors.first_name.message}</p>}
          </div>
          <div>
            <label className="label">Nom</label>
            <input {...register("last_name")} className="input" />
          </div>
        </div>
        <div>
          <label className="label">Email *</label>
          <input {...register("email")} type="email" className="input" />
          {errors.email && <p className="text-xs text-red-500 mt-0.5">{errors.email.message}</p>}
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="label">Téléphone</label>
            <input {...register("phone")} className="input" />
          </div>
          <div>
            <label className="label">Matricule Assabil</label>
            <input {...register("matricule")} className="input" placeholder="Ex: MAT001" />
          </div>
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="label">Rôle</label>
            <select {...register("role")} className="input">
              {ROLES.map((r) => <option key={r} value={r}>{r}</option>)}
            </select>
          </div>
          <div>
            <label className="label">Mode paiement</label>
            <select {...register("payment_mode")} className="input">
              {PAYMENT_MODES.map((m) => <option key={m} value={m}>{PAYMENT_LABELS[m]}</option>)}
            </select>
          </div>
        </div>
        <div>
          <label className="label">Plafond mensuel (MAD, vide = illimité)</label>
          <input
            {...register("plafond_mensuel", { setValueAs: (v) => v === "" ? null : parseFloat(v) })}
            type="number" step="0.01" className="input"
          />
        </div>
        <OrgFields control={control as unknown as Control<OrgFormFields>} setValue={setValue as unknown as UseFormSetValue<OrgFormFields>} idPrefix="create-user" />
        <div className="flex justify-end gap-2 pt-2">
          <button type="button" onClick={onClose} className="btn-secondary">Annuler</button>
          <button type="submit" disabled={create.isPending} className="btn-primary">
            {create.isPending ? "Création..." : "Créer"}
          </button>
        </div>
      </form>
    </Modal>
  );
}

function EditUserModal({ user: initialUser, open, onClose }: { user: User | null; open: boolean; onClose: () => void }) {
  const qc = useQueryClient();
  const { user: currentUser } = useAuth();
  const isAdmin = currentUser?.role === "admin";

  const { data: user } = useQuery<User>({
    queryKey: ["user", initialUser?.id],
    queryFn: () => api.get(`/users/${initialUser!.id}`).then((r) => r.data),
    enabled: !!initialUser && open,
    initialData: initialUser ?? undefined,
  });

  const { register, handleSubmit, control, setValue } = useForm<EditForm>({
    resolver: zodResolver(editSchema),
    values: user ? {
      first_name: user.first_name ?? "",
      last_name: user.last_name ?? "",
      phone: user.phone ?? "",
      matricule: user.matricule ?? "",
      productsalesgroup_code: user.productsalesgroup_code ?? "",
      societe: user.societe ?? "",
      agence: user.agence ?? "",
      ville: user.ville ?? "",
    } : undefined,
  });

  const [role, setRole] = useState<User["role"]>(user?.role ?? "acheteur");
  const [plafond, setPlafond] = useState<string>(user?.plafond_mensuel?.toString() ?? "");
  const [newPassword, setNewPassword] = useState("");

  useEffect(() => {
    if (user) {
      setRole(user.role);
      setPlafond(user.plafond_mensuel?.toString() ?? "");
    }
  }, [user]);

  const update = useMutation({
    mutationFn: (d: EditForm) => api.put(`/users/${user!.id}`, d),
    onSuccess: () => { toast.success("Profil mis à jour"); qc.invalidateQueries({ queryKey: ["users"] }); },
    onError: (e) => toast.error(getErrorMessage(e, "Erreur")),
  });

  const updateRole = useMutation({
    mutationFn: (r: string) => api.patch(`/users/${user!.id}/role`, { role: r }),
    onSuccess: () => { toast.success("Rôle mis à jour"); qc.invalidateQueries({ queryKey: ["users"] }); },
    onError: (e) => toast.error(getErrorMessage(e, "Erreur")),
  });

  const updatePlafond = useMutation({
    mutationFn: (val: number | null) => api.patch(`/users/${user!.id}/plafond`, { plafond_mensuel: val }),
    onSuccess: () => { toast.success("Plafond mis à jour"); qc.invalidateQueries({ queryKey: ["users"] }); },
    onError: (e) => toast.error(getErrorMessage(e, "Erreur")),
  });

  const updatePaymentMode = useMutation({
    mutationFn: (modes: string[]) => api.put(`/payment-methods/${user!.id}/modes`, { modes }),
    onSuccess: () => { toast.success("Modes de paiement mis à jour"); qc.invalidateQueries({ queryKey: ["users"] }); },
    onError: (e) => toast.error(getErrorMessage(e, "Erreur")),
  });

  const setPassword = useMutation({
    mutationFn: (pw: string) => api.patch(`/users/${user!.id}/set-password`, { new_password: pw }),
    onSuccess: () => { toast.success("Mot de passe mis à jour"); setNewPassword(""); },
    onError: (e) => toast.error(getErrorMessage(e, "Erreur")),
  });

  const { data: plafondStatus } = useQuery<PlafondStatus>({
    queryKey: ["plafond", user?.id],
    queryFn: () => api.get(`/users/${user!.id}/plafond/status`).then((r) => r.data),
    enabled: !!user && open && isAdmin,
  });

  if (!user) return null;

  const title = isAdmin ? `Modifier — ${user.email}` : `Fiche utilisateur — ${user.email}`;

  return (
    <Modal open={open} onClose={onClose} title={title} size="lg">
      {/* Profile fields — editable by admin only */}
      {isAdmin ? (
        <form onSubmit={handleSubmit((d) => update.mutate(d))} className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <div><label className="label">Prénom</label><input {...register("first_name")} className="input" /></div>
            <div><label className="label">Nom</label><input {...register("last_name")} className="input" /></div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div><label className="label">Téléphone</label><input {...register("phone")} className="input" /></div>
            <div><label className="label">Matricule Assabil</label><input {...register("matricule")} className="input" /></div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div className="col-span-2"><OrgFields control={control as unknown as Control<OrgFormFields>} setValue={setValue as unknown as UseFormSetValue<OrgFormFields>} idPrefix="edit-user" /></div>
          </div>
          <div><label className="label">PSG Code</label><input {...register("productsalesgroup_code")} className="input" /></div>

          {/* Admin-only fields */}
          <div className="grid grid-cols-2 gap-3 border-t pt-3">
            <div>
              <label className="label">Rôle</label>
              <div className="flex gap-2">
                <select value={role} onChange={(e) => setRole(e.target.value as User["role"])} className="input flex-1">
                  {ROLES.map((r) => <option key={r} value={r}>{r}</option>)}
                </select>
                <button type="button" onClick={() => updateRole.mutate(role)} disabled={role === user.role || updateRole.isPending} className="btn-secondary btn-sm">OK</button>
              </div>
            </div>
            <div>
              <label className="label">Plafond mensuel (MAD)</label>
              <div className="flex gap-2">
                <input value={plafond} onChange={(e) => setPlafond(e.target.value)} type="number" step="0.01" placeholder="Illimité" className="input flex-1" />
                <button type="button" onClick={() => updatePlafond.mutate(plafond === "" ? null : parseFloat(plafond))} disabled={updatePlafond.isPending} className="btn-secondary btn-sm">OK</button>
              </div>
              {plafondStatus && (
                <p className="text-xs text-madec-muted mt-1">
                  Dépensé : {plafondStatus.spent_this_month.toFixed(2)} MAD
                  {plafondStatus.remaining != null && ` — Restant : ${plafondStatus.remaining.toFixed(2)} MAD`}
                </p>
              )}
            </div>
            <div className="col-span-2">
              <label className="label">Modes de paiement (plusieurs possibles)</label>
              <div className="mt-1 flex flex-wrap gap-2">
                {ATOMIC_PAYMENT_MODES.map((m) => {
                  const on = expandPaymentModes(user.payment_mode).includes(m);
                  return (
                    <label
                      key={m}
                      className={`inline-flex cursor-pointer items-center gap-1.5 rounded border px-2.5 py-1.5 text-xs ${
                        on ? "border-madec-primary bg-madec-primary text-white" : "border-madec-border bg-white"
                      }`}
                    >
                      <input
                        type="checkbox"
                        className="sr-only"
                        checked={on}
                        disabled={updatePaymentMode.isPending}
                        onChange={() => {
                          const cur = expandPaymentModes(user.payment_mode);
                          const next = on ? cur.filter((x) => x !== m) : [...cur, m];
                          if (next.length === 0) {
                            toast.error("Au moins un mode est requis");
                            return;
                          }
                          updatePaymentMode.mutate(next);
                        }}
                      />
                      {m === "deduction_salaire" ? "Déduction" : PAYMENT_LABELS[m]}
                    </label>
                  );
                })}
                <button
                  type="button"
                  title="Activer tous les modes (espèces, carte, déduction)"
                  disabled={
                    updatePaymentMode.isPending ||
                    expandPaymentModes(user.payment_mode).length === ATOMIC_PAYMENT_MODES.length
                  }
                  onClick={() => updatePaymentMode.mutate([...ATOMIC_PAYMENT_MODES])}
                  className="rounded border border-madec-border bg-white px-2.5 py-1.5 text-xs font-semibold hover:border-madec-primary hover:bg-madec-active disabled:cursor-default disabled:opacity-60"
                >
                  Tous
                </button>
              </div>
              <p className="mt-1 text-xs text-madec-muted">{paymentModeLabel(user.payment_mode)}</p>
            </div>
            <div className="col-span-2">
              <label className="label">Changer le mot de passe (manuel)</label>
              <div className="flex gap-2">
                <input
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  type="text"
                  autoComplete="new-password"
                  placeholder="Nouveau mot de passe"
                  className="input flex-1"
                />
                <button
                  type="button"
                  onClick={() => setPassword.mutate(newPassword)}
                  disabled={newPassword.length < 8 || setPassword.isPending}
                  className="btn-secondary btn-sm"
                >
                  {setPassword.isPending ? "..." : "Définir"}
                </button>
              </div>
              <p className="mt-1 text-xs text-madec-muted">
                Min. 8 caractères, avec majuscule, minuscule et chiffre. L’utilisateur est notifié par email.
              </p>
            </div>
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <button type="button" onClick={onClose} className="btn-secondary">Fermer</button>
            <button type="submit" disabled={update.isPending} className="btn-primary">
              {update.isPending ? "Enregistrement..." : "Enregistrer"}
            </button>
          </div>
        </form>
      ) : (
        /* Gestionnaire: read-only view */
        <div className="space-y-3 text-sm">
          <div className="grid grid-cols-2 gap-3">
            <div><p className="label">Prénom</p><p className="font-medium">{user.first_name ?? "—"}</p></div>
            <div><p className="label">Nom</p><p className="font-medium">{user.last_name ?? "—"}</p></div>
            <div><p className="label">Email</p><p>{user.email}</p></div>
            <div><p className="label">Téléphone</p><p>{user.phone ?? "—"}</p></div>
            <div><p className="label">Matricule</p><p className="font-mono">{user.matricule ?? "—"}</p></div>
            <div><p className="label">Rôle</p><span className="badge bg-madec-tint text-madec-text">{user.role}</span></div>
            <div><p className="label">Société</p><p>{user.societe ?? "—"}</p></div>
            <div><p className="label">Agence</p><p>{user.agence ?? "—"}</p></div>
            <div><p className="label">Ville</p><p>{user.ville ?? "—"}</p></div>
            <div><p className="label">Modes paiement</p><p>{paymentModeLabel(user.payment_mode)}</p></div>
            <div><p className="label">Plafond</p><p>{user.plafond_mensuel != null ? `${user.plafond_mensuel} MAD` : "Illimité"}</p></div>
          </div>
          {user.synced_from_intermediate && (
            <p className="text-xs text-madec-muted">Synchronisé depuis la base intermédiaire</p>
          )}
          <div className="flex justify-end pt-2">
            <button type="button" onClick={onClose} className="btn-secondary">Fermer</button>
          </div>
        </div>
      )}
    </Modal>
  );
}

function UserOrdersModal({ user, open, onClose }: { user: User | null; open: boolean; onClose: () => void }) {
  const [page, setPage] = useState(1);
  const { data, isLoading } = useQuery<PaginatedResponse<Order>>({
    queryKey: ["user-orders", user?.id, page],
    queryFn: () => api.get(`/users/${user!.id}/orders?page=${page}`).then((r) => r.data),
    enabled: !!user && open,
  });

  if (!user) return null;

  return (
    <Modal open={open} onClose={onClose} title={`Commandes — ${user.first_name ?? ""} ${user.last_name ?? ""}`.trim() || user.email} size="lg">
      {isLoading ? <PageLoader /> : (
        <div className="space-y-2">
          {data?.items.length === 0 ? (
            <p className="text-sm text-madec-muted text-center py-4">Aucune commande</p>
          ) : (
            data?.items.map((o) => (
              <div key={o.id} className="flex items-center justify-between rounded-lg bg-madec-surface px-3 py-2 text-sm">
                <div>
                  <p className="font-mono text-xs">{o.sorder_code}</p>
                  <p className="text-xs text-madec-muted">{format(new Date(o.created_at), "d MMM yyyy", { locale: fr })}</p>
                </div>
                <div className="text-right">
                  <StatusBadge status={o.sorder_status} />
                  <p className="font-semibold mt-0.5">{Number(o.dueamount).toFixed(2)} MAD</p>
                </div>
              </div>
            ))
          )}
          {data && data.pages > 1 && (
            <Pagination page={data.page} pages={data.pages} total={data.total} pageSize={data.page_size} onChange={setPage} />
          )}
        </div>
      )}
    </Modal>
  );
}

export function UsersPage() {
  const qc = useQueryClient();
  const { isAdmin, role } = useRole();

  const [page, setPage]     = useState(1);
  const [search, setSearch] = useState("");
  const [roleFilter, setRoleFilter] = useState("");
  const [createOpen, setCreateOpen] = useState(false);
  const [editUser, setEditUser] = useState<User | null>(null);
  const [ordersUser, setOrdersUser] = useState<User | null>(null);
  const [confirmToggle, setConfirmToggle] = useState<User | null>(null);
  const [confirmReset, setConfirmReset] = useState<User | null>(null);

  const { data, isLoading } = useQuery<PaginatedResponse<User>>({
    queryKey: ["users", page, search, roleFilter],
    queryFn: () => {
      const params = new URLSearchParams({
        page: String(page),
        page_size: String(USER_PAGE_SIZE),
      });
      if (search) params.set("search", search);
      if (roleFilter) params.set("role", roleFilter);
      return api.get(`/users?${params}`).then((r) => r.data);
    },
  });

  const toggle = useMutation({
    mutationFn: (id: number) => api.patch(`/users/${id}/toggle`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["users"] }),
    onError: (e) => toast.error(getErrorMessage(e, "Erreur")),
  });

  const resetPw = useMutation({
    mutationFn: (id: number) => api.patch(`/users/${id}/reset-password`),
    onSuccess: () => toast.success("Nouveau mot de passe envoyé par email"),
    onError: (e) => toast.error(getErrorMessage(e, "Erreur")),
  });

  const [bulkPlafond, setBulkPlafond] = useState("");
  const [confirmBulk, setConfirmBulk] = useState(false);
  const [defaultPlafond, setDefaultPlafond] = useState("");

  const { data: defaultPlafondData } = useQuery<{ plafond_mensuel: number | null }>({
    queryKey: ["settings-default-plafond"],
    queryFn: () => api.get("/settings/default-plafond").then((r) => r.data),
    enabled: isAdmin,
  });

  useEffect(() => {
    if (defaultPlafondData) {
      setDefaultPlafond(
        defaultPlafondData.plafond_mensuel != null
          ? String(defaultPlafondData.plafond_mensuel)
          : "",
      );
    }
  }, [defaultPlafondData]);

  const saveDefaultPlafond = useMutation({
    mutationFn: (val: number | null) =>
      api.put("/settings/default-plafond", { plafond_mensuel: val }),
    onSuccess: () => {
      toast.success("Plafond par défaut enregistré");
      qc.invalidateQueries({ queryKey: ["settings-default-plafond"] });
    },
    onError: (e) => toast.error(getErrorMessage(e, "Erreur")),
  });

  const bulkPlafondMut = useMutation({
    mutationFn: (val: number | null) => api.patch("/users/plafond/bulk", { plafond_mensuel: val }),
    onSuccess: (res) => {
      toast.success(res.data?.message ?? "Plafond appliqué à tous les acheteurs");
      qc.invalidateQueries({ queryKey: ["users"] });
      setConfirmBulk(false);
    },
    onError: (e) => toast.error(getErrorMessage(e, "Erreur")),
  });

  if (isLoading && !data) return <PageLoader />;

  return (
    <div className="page-content max-w-7xl space-y-4">
      <PageHeader
        title="Utilisateurs"
        actions={
          isAdmin ? (
            <button className="btn-primary btn-sm" onClick={() => setCreateOpen(true)}>
              <Plus size={14} /> Créer
            </button>
          ) : undefined
        }
      />

      {role && (role === "admin" || role === "gestionnaire") && (
        <StaffScopeBanner page="users" role={role} />
      )}

      {isAdmin && (
        <div className="space-y-3">
          <div className="flex flex-wrap items-end gap-3 rounded-lg border border-madec-border bg-madec-active/40 p-3">
            <div className="flex-1 min-w-48">
              <label className="label">Plafond par défaut (nouvelles créations)</label>
              <input
                type="number"
                step="0.01"
                min="0"
                className="input"
                placeholder="Vide = illimité"
                value={defaultPlafond}
                onChange={(e) => setDefaultPlafond(e.target.value)}
              />
              <p className="mt-1 text-[11px] text-madec-muted">
                Appliqué automatiquement aux nouveaux acheteurs (admin + sync ETL) si aucun plafond n’est saisi.
              </p>
            </div>
            <button
              type="button"
              className="btn-primary btn-sm"
              disabled={saveDefaultPlafond.isPending}
              onClick={() =>
                saveDefaultPlafond.mutate(
                  defaultPlafond.trim() === "" ? null : parseFloat(defaultPlafond),
                )
              }
            >
              Enregistrer
            </button>
          </div>
          <div className="flex flex-wrap items-end gap-3 rounded-lg border border-madec-border bg-madec-active/40 p-3">
            <div className="flex-1 min-w-48">
              <label className="label">Plafond mensuel — appliquer à tous les acheteurs</label>
              <input
                type="number" step="0.01" min="0" className="input"
                placeholder="Vide = illimité"
                value={bulkPlafond}
                onChange={(e) => setBulkPlafond(e.target.value)}
              />
            </div>
            <button
              type="button" className="btn-secondary btn-sm"
              disabled={bulkPlafondMut.isPending}
              onClick={() => setConfirmBulk(true)}
            >
              Appliquer à tous
            </button>
          </div>
        </div>
      )}

      <div className="flex flex-wrap gap-3">
        <div className="relative flex-1 min-w-48">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-madec-muted" />
          <input
            className="input pl-9" placeholder="Nom, email..."
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1); }}
          />
        </div>
        <select className="input w-40" value={roleFilter} onChange={(e) => { setRoleFilter(e.target.value); setPage(1); }}>
          <option value="">Tous les rôles</option>
          {ROLES.map((r) => <option key={r} value={r}>{r}</option>)}
        </select>
      </div>

      {data && data.total > 0 && (
        <div className="flex flex-wrap items-center justify-between gap-2">
          <p className="text-sm text-madec-muted">
            <span className="font-semibold text-madec-text">{data.total}</span>
            {" "}utilisateur{data.total > 1 ? "s" : ""}
          </p>
          <p className="text-xs text-madec-muted">{USER_PAGE_SIZE} par page</p>
        </div>
      )}

      <div className="card !p-0 overflow-hidden">
        <div className="overflow-x-auto">
        <table className="data-table !rounded-none !border-0 !shadow-none">
          <thead>
            <tr>
              <th>Nom / Email</th>
              <th>Rôle</th>
              <th>Paiement</th>
              <th>Plafond</th>
              <th>Statut</th>
              <th className="w-28" />
            </tr>
          </thead>
          <tbody>
            {data?.items.map((u) => (
              <tr key={u.id}>
                <td>
                  <p className="font-medium text-madec-text">{u.first_name} {u.last_name}</p>
                  <p className="text-xs text-madec-muted">{u.email}</p>
                  {u.societe && <p className="text-xs text-madec-muted/80">{u.societe}{u.agence ? ` · ${u.agence}` : ""}</p>}
                  {u.matricule && <p className="text-xs font-mono text-madec-muted/80">{u.matricule}</p>}
                </td>
                <td><span className="badge bg-madec-tint text-madec-text">{u.role}</span></td>
                <td className="text-madec-secondary">{paymentModeLabel(u.payment_mode)}</td>
                <td className="text-madec-secondary">{u.plafond_mensuel != null ? `${u.plafond_mensuel} MAD` : "∞"}</td>
                <td><StatusBadge status={u.is_active ? "active" : "inactive"} /></td>
                <td>
                  <div className="flex items-center gap-2">
                    {/* Admin: edit; Gestionnaire: read-only view */}
                    <button
                      title={isAdmin ? "Modifier" : "Voir"}
                      onClick={() => setEditUser(u)}
                      className="text-madec-muted hover:text-madec-primary"
                    >
                      {isAdmin ? <Pencil size={15} /> : <Eye size={15} />}
                    </button>
                    <button title="Commandes" onClick={() => setOrdersUser(u)} className="text-madec-muted hover:text-madec-primary">
                      <Eye size={15} />
                    </button>
                    {isAdmin && (
                      <>
                        <button
                          title={u.is_active ? "Désactiver" : "Activer"}
                          onClick={() => setConfirmToggle(u)}
                          className="text-madec-muted hover:text-madec-primary"
                        >
                          {u.is_active ? <ToggleRight size={18} /> : <ToggleLeft size={18} />}
                        </button>
                        <button
                          title="Réinitialiser le mot de passe"
                          onClick={() => setConfirmReset(u)}
                          className="text-madec-muted hover:text-yellow-600"
                        >
                          <KeyRound size={16} />
                        </button>
                      </>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        </div>
        {data && (
          <Pagination
            page={data.page}
            pages={data.pages}
            total={data.total}
            pageSize={USER_PAGE_SIZE}
            onChange={setPage}
          />
        )}
      </div>

      {isAdmin && <CreateUserModal open={createOpen} onClose={() => setCreateOpen(false)} />}
      <EditUserModal user={editUser} open={!!editUser} onClose={() => setEditUser(null)} />
      <UserOrdersModal user={ordersUser} open={!!ordersUser} onClose={() => setOrdersUser(null)} />

      <ConfirmModal
        open={!!confirmToggle}
        title={confirmToggle?.is_active ? "Désactiver le compte" : "Activer le compte"}
        message={
          confirmToggle?.is_active
            ? `Désactiver le compte de ${confirmToggle.first_name ?? confirmToggle.email} ? L'utilisateur ne pourra plus se connecter.`
            : `Réactiver le compte de ${confirmToggle?.first_name ?? confirmToggle?.email} ?`
        }
        confirmLabel={confirmToggle?.is_active ? "Désactiver" : "Activer"}
        danger={confirmToggle?.is_active}
        onConfirm={() => confirmToggle && toggle.mutate(confirmToggle.id)}
        onClose={() => setConfirmToggle(null)}
      />

      <ConfirmModal
        open={!!confirmReset}
        title="Réinitialiser le mot de passe"
        message={`Un nouveau mot de passe sera généré et envoyé par email à ${confirmReset?.email}. Continuer ?`}
        confirmLabel="Réinitialiser"
        danger
        onConfirm={() => confirmReset && resetPw.mutate(confirmReset.id)}
        onClose={() => setConfirmReset(null)}
      />

      <ConfirmModal
        open={confirmBulk}
        title="Appliquer le plafond à tous"
        message={
          bulkPlafond === ""
            ? "Définir un plafond ILLIMITÉ pour TOUS les acheteurs ? Cela remplace les plafonds individuels existants."
            : `Appliquer un plafond de ${bulkPlafond} DH à TOUS les acheteurs ? Cela remplace les plafonds individuels existants.`
        }
        confirmLabel="Appliquer à tous"
        danger
        onConfirm={() => bulkPlafondMut.mutate(bulkPlafond === "" ? null : parseFloat(bulkPlafond))}
        onClose={() => setConfirmBulk(false)}
      />
    </div>
  );
}
