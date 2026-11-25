import { useNavigate } from "react-router-dom";
import { ShieldOff } from "lucide-react";

export function ForbiddenPage() {
  const navigate = useNavigate();
  return (
    <div className="flex h-full min-h-[60vh] flex-col items-center justify-center gap-4 text-center px-4">
      <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-madec-dangerTint text-madec-danger">
        <ShieldOff size={32} />
      </div>
      <div>
        <h1 className="text-xl font-bold text-madec-text">Accès interdit</h1>
        <p className="mt-2 text-sm text-madec-muted max-w-xs">
          Vous n&apos;avez pas les droits nécessaires pour accéder à cette page.
        </p>
      </div>
      <button
        type="button"
        onClick={() => navigate("/dashboard")}
        className="btn-secondary mt-2"
      >
        Retour au tableau de bord
      </button>
    </div>
  );
}
