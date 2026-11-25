import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { Link } from "react-router-dom";
import toast from "react-hot-toast";
import api from "../lib/api";
import { getErrorMessage } from "../lib/errors";
import { Spinner } from "../components/ui/Spinner";
import { AuthShell } from "../components/layout/AuthShell";

const schema = z.object({ email: z.string().email("Email invalide") });
type Form = z.infer<typeof schema>;

export function ForgotPasswordPage() {
  const [sent, setSent] = useState(false);
  const { register, handleSubmit, formState: { errors } } = useForm<Form>({ resolver: zodResolver(schema) });

  const send = useMutation({
    mutationFn: (d: Form) => api.post("/auth/reset-password/request", d),
    onSuccess: () => setSent(true),
    onError: (e) => toast.error(getErrorMessage(e, "Impossible d'envoyer l'email")),
  });

  return (
    <AuthShell
      title="Mot de passe oublié"
      subtitle="Entrez votre email — nous vous enverrons un code de réinitialisation"
    >
      {sent ? (
        <div className="py-2 text-center">
          <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-green-100 text-green-600 text-xl">
            ✓
          </div>
          <p className="font-semibold text-madec-text">Email envoyé</p>
          <p className="mt-2 text-sm text-madec-muted">
            Vérifiez votre boîte mail et suivez les instructions.
          </p>
          <Link to="/reset-password" className="link-brand mt-4 inline-block text-sm">
            J&apos;ai reçu mon code →
          </Link>
          <Link to="/login" className="mt-3 block text-sm text-madec-muted hover:text-madec-text">
            Retour à la connexion
          </Link>
        </div>
      ) : (
        <form onSubmit={handleSubmit((d) => send.mutate(d))} className="space-y-5">
          <div>
            <label className="label">Adresse email</label>
            <input {...register("email")} type="email" className="input" placeholder="vous@exemple.com" />
            {errors.email && <p className="mt-1.5 text-xs text-red-500">{errors.email.message}</p>}
          </div>
          <button type="submit" disabled={send.isPending} className="btn-primary w-full">
            {send.isPending ? <Spinner size="sm" /> : "Envoyer le code"}
          </button>
          <Link to="/login" className="block text-center text-sm text-madec-muted hover:text-madec-text">
            Retour
          </Link>
        </form>
      )}
    </AuthShell>
  );
}
