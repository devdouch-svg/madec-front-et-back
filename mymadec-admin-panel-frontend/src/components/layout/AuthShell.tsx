import type { ReactNode } from "react";
import { Package, Shield, Truck } from "lucide-react";
import { Logo } from "../brand/Logo";

interface AuthShellProps {
  children: ReactNode;
  title: string;
  subtitle?: string;
}

export function AuthShell({ children, title, subtitle }: AuthShellProps) {
  return (
    <div className="flex min-h-screen">
      <div className="relative hidden overflow-hidden bg-gradient-to-br from-primary-800 via-primary-600 to-primary-500 lg:flex lg:w-[44%] xl:w-[42%]">
        <div
          className="pointer-events-none absolute inset-0 opacity-25"
          style={{
            backgroundImage:
              "radial-gradient(circle at 15% 85%, rgba(255,255,255,0.2) 0%, transparent 50%), radial-gradient(circle at 85% 15%, rgba(255,255,255,0.15) 0%, transparent 45%)",
          }}
        />
        <div className="relative z-10 flex flex-col justify-between p-10 xl:p-14">
          <div>
            <Logo on="dark" className="auth-logo mb-10" />
            <p className="max-w-sm text-base leading-relaxed text-primary-100/90">
              Plateforme de commande B2B — alimentaire et non alimentaire.
            </p>
          </div>

          <ul className="space-y-4">
            {[
              { icon: <Package size={20} />, text: "Catalogue alimentaire et non alimentaire" },
              { icon: <Truck size={20} />, text: "Suivi des commandes en temps réel" },
              { icon: <Shield size={20} />, text: "Accès sécurisé par rôle" },
            ].map((item) => (
              <li key={item.text} className="flex items-center gap-3 text-sm text-primary-50">
                <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-white/10 ring-1 ring-white/15">
                  {item.icon}
                </span>
                {item.text}
              </li>
            ))}
          </ul>

          <p className="text-xs text-primary-300/70">© My Madec — usage professionnel</p>
        </div>
      </div>

      <div className="flex flex-1 flex-col items-center justify-center bg-white p-6 sm:p-10">
        <div className="mb-8 lg:hidden">
          <Logo on="light" className="auth-logo mx-auto" />
        </div>

        <div className="w-full max-w-md">
          <div className="mb-6 text-center lg:text-left">
            <h1 className="text-2xl font-bold tracking-tight text-madec-text">{title}</h1>
            {subtitle && <p className="mt-2 text-sm text-madec-muted">{subtitle}</p>}
          </div>

          <div className="card">{children}</div>
        </div>
      </div>
    </div>
  );
}
