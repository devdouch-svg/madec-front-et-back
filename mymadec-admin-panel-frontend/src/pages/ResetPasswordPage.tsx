import { useEffect, useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { Link, useSearchParams, useNavigate } from "react-router-dom";
import api from "../lib/api";
import { getErrorMessage } from "../lib/errors";
import { PASSWORD_HINT, passwordField } from "../lib/password";
import { Spinner } from "../components/ui/Spinner";
import { AuthShell } from "../components/layout/AuthShell";

const schema = z.object({
  token: z.string().min(1, "Code requis"),
  new_password: passwordField,
  confirm_password: z.string().min(1, "Requis"),
}).refine((d) => d.new_password === d.confirm_password, {
  message: "Les mots de passe ne correspondent pas",
  path: ["confirm_password"],
});
type Form = z.infer<typeof schema>;

export function ResetPasswordPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();
  const [done, setDone] = useState(false);
  const [tokenFromUrl] = useState(() => searchParams.get("token") ?? "");

  const { register, handleSubmit, setValue, formState: { errors } } = useForm<Form>({
    resolver: zodResolver(schema),
    defaultValues: { token: tokenFromUrl },
  });

  useEffect(() => {
    if (!searchParams.get("token")) return;
    setValue("token", searchParams.get("token") ?? "");
    setSearchParams({}, { replace: true });
  }, [searchParams, setSearchParams, setValue]);

  const confirm = useMutation({
    mutationFn: (d: Form) =>
      api.post("/auth/reset-password/confirm", { token: d.token, new_password: d.new_password }),
    onSuccess: () => setDone(true),
  });

  return (
    <AuthShell title="Nouveau mot de passe" subtitle="Entrez le code reçu par email">
      {done ? (
        <div className="py-2 text-center">
          <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-green-100 text-green-600 text-xl">
            ✓
          </div>
          <p className="font-semibold text-madec-text">Mot de passe réinitialisé</p>
          <button onClick={() => navigate("/login")} className="btn-primary mt-5 w-full">
            Se connecter
          </button>
        </div>
      ) : (
        <form onSubmit={handleSubmit((d) => confirm.mutate(d))} className="space-y-4">
          <div>
            <label className="label">Code de réinitialisation</label>
            <input {...register("token")} className="input" placeholder="Code reçu par email" />
            {errors.token && <p className="mt-1.5 text-xs text-red-500">{errors.token.message}</p>}
          </div>
          <div>
            <label className="label">Nouveau mot de passe</label>
            <input {...register("new_password")} type="password" className="input" autoComplete="new-password" />
            <p className="mt-1.5 text-xs text-madec-muted">{PASSWORD_HINT}</p>
            {errors.new_password && <p className="mt-1.5 text-xs text-red-500">{errors.new_password.message}</p>}
          </div>
          <div>
            <label className="label">Confirmer le mot de passe</label>
            <input {...register("confirm_password")} type="password" className="input" />
            {errors.confirm_password && <p className="mt-1.5 text-xs text-red-500">{errors.confirm_password.message}</p>}
          </div>
          {confirm.isError && (
            <p className="rounded-lg bg-red-50 px-3 py-2 text-xs text-red-600">
              {getErrorMessage(confirm.error, "Code invalide ou expiré")}
            </p>
          )}
          <button type="submit" disabled={confirm.isPending} className="btn-primary w-full">
            {confirm.isPending ? <Spinner size="sm" /> : "Réinitialiser"}
          </button>
          <Link to="/login" className="block text-center text-sm text-madec-muted hover:text-madec-text">
            Retour
          </Link>
        </form>
      )}
    </AuthShell>
  );
}
