import { Modal } from "./Modal";

interface Props {
  open: boolean;
  title: string;
  message: string;
  confirmLabel?: string;
  danger?: boolean;
  onConfirm: () => void;
  onClose: () => void;
}

export function ConfirmModal({
  open, title, message, confirmLabel = "Confirmer",
  danger = false, onConfirm, onClose,
}: Props) {
  return (
    <Modal open={open} onClose={onClose} title={title} size="sm">
      <p className="text-sm text-madec-secondary">{message}</p>
      <div className="flex justify-end gap-2 mt-5">
        <button type="button" onClick={onClose} className="btn-secondary">
          Annuler
        </button>
        <button
          type="button"
          onClick={() => { onConfirm(); onClose(); }}
          className={danger ? "btn-danger" : "btn-primary"}
        >
          {confirmLabel}
        </button>
      </div>
    </Modal>
  );
}
