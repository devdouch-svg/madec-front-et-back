import { AlertCircle, RefreshCw } from "lucide-react";

interface ErrorStateProps {
  message?: string;
  onRetry?: () => void;
}

export function ErrorState({
  message = "Impossible de charger les données. Vérifiez votre connexion et réessayez.",
  onRetry,
}: ErrorStateProps) {
  return (
    <div className="empty-state border-madec-dangerTint bg-madec-dangerTint/30">
      <div className="empty-state-icon !bg-madec-dangerTint !text-madec-danger">
        <AlertCircle size={28} strokeWidth={1.5} />
      </div>
      <p className="empty-state-title text-madec-danger">Erreur de chargement</p>
      <p className="empty-state-desc text-madec-danger/90">{message}</p>
      {onRetry && (
        <button type="button" onClick={onRetry} className="btn-secondary mt-4">
          <RefreshCw size={16} />
          Réessayer
        </button>
      )}
    </div>
  );
}
