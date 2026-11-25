import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useNavigate, Navigate, Link } from "react-router-dom";
import { Eye, EyeOff } from "lucide-react";
import toast from "react-hot-toast";
import { useAuth } from "../store/auth";
import { getErrorMessage } from "../lib/errors";
import { Spinner } from "../components/ui/Spinner";
import { AuthShell } from "../components/layout/AuthShell";

const schema = z.object({
  matricule: z.string().min(1, "Identifiant requis"),
  password:  z.string().min(1, "Mot de passe requis"),
});
type FormData = z.infer<typeof schema>;

const DEV_ACCOUNTS = [
  { matricule: "ADMIN001", role: "Administrateur" },
  { matricule: "ACH001", role: "Acheteur" },
  { matricule: "GEST001", role: "Gestionnaire" },
] as const;

const DEV_PASSWORD = "Test1234!";

export function LoginPage() {
  const { login, isLoading, user } = useAuth();
  const navigate = useNavigate();
  const [showPassword, setShowPassword] = useState(false);

  const { register, handleSubmit, setValue, formState: { errors } } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: { matricule: "", password: "" },
  });

  if (user) return <Navigate to="/dashboard" replace />;

  const onSubmit = async (data: FormData) => {
    try {
      await login(data.matricule.trim(), data.password);
      navigate("/dashboard");
    } catch (e: unknown) {
      toast.error(getErrorMessage(e, "Identifiants incorrects"));
    }
  };

  const fillDemo = (matricule: string) => {
    setValue("matricule", matricule);
    setValue("password", DEV_PASSWORD);
  };

  return (
    <AuthShell title="Connexion" subtitle="Connectez-vous à votre compte professionnel My Madec">
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
        <div>
          <label className="label" htmlFor="login-matricule">Identifiant (USER_LOGIN)</label>
          <input
            id="login-matricule"
            {...register("matricule")}
            type="text"
            className="input"
            placeholder="Identifiant Assabil"
            autoComplete="username"
          />
          {errors.matricule && <p className="mt-1.5 text-xs text-red-500">{errors.matricule.message}</p>}
          <p className="mt-1 text-[11px] text-madec-muted">USER_LOGIN Assabil (matricule / email aussi acceptés)</p>
        </div>

        <div>
          <label className="label" htmlFor="login-password">Mot de passe</label>
          <div className="relative">
            <input
              id="login-password"
              {...register("password")}
              type={showPassword ? "text" : "password"}
              className="input pr-11"
              placeholder="••••••••"
              autoComplete="current-password"
            />
            <button
              type="button"
              onClick={() => setShowPassword((v) => !v)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-madec-muted transition-colors hover:text-madec-text"
              aria-label={showPassword ? "Masquer le mot de passe" : "Afficher le mot de passe"}
            >
              {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
            </button>
          </div>
          {errors.password && <p className="mt-1.5 text-xs text-red-500">{errors.password.message}</p>}
        </div>

        <button type="submit" disabled={isLoading} className="btn-primary w-full">
          {isLoading ? <Spinner size="sm" /> : "Se connecter"}
        </button>
      </form>

      <div className="mt-5 border-t border-madec-border pt-5 text-center">
        <Link to="/forgot-password" className="link-brand text-sm">
          Mot de passe oublié ?
        </Link>
      </div>

      {import.meta.env.DEV && (
        <div className="mt-5 rounded-xl border border-madec-tint/80 bg-gradient-to-b from-madec-active to-white p-4 text-left">
          <p className="text-xs font-semibold uppercase tracking-wide text-madec-primary">Environnement de développement</p>
          <p className="mt-2 text-sm text-madec-secondary">
            Mot de passe commun : <code className="rounded bg-white px-1.5 py-0.5 font-mono text-xs text-madec-primary ring-1 ring-madec-tint">{DEV_PASSWORD}</code>
          </p>
          <ul className="mt-3 space-y-2">
            {DEV_ACCOUNTS.map((acc) => (
              <li key={acc.matricule}>
                <button
                  type="button"
                  onClick={() => fillDemo(acc.matricule)}
                  className="flex w-full items-center justify-between rounded-lg border border-madec-border/80 bg-white px-3 py-2 text-left text-sm transition-colors hover:border-madec-light hover:bg-madec-active/50"
                >
                  <span className="font-mono text-xs text-madec-text">{acc.matricule}</span>
                  <span className="text-xs text-madec-muted">{acc.role}</span>
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}
    </AuthShell>
  );
}
