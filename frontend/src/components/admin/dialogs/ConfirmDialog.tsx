"use client";

import { useEffect, useRef } from "react";

type Props = {
  open: boolean;
  title: string;
  description?: string;
  confirmText?: string;
  cancelText?: string;
  variant?: "danger" | "default";
  onConfirm: () => void;
  onCancel: () => void;
};

export default function ConfirmDialog({
  open,
  title,
  description,
  confirmText = "Confirmer",
  cancelText = "Annuler",
  variant = "default",
  onConfirm,
  onCancel,
}: Props) {
  const panelRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!open) return;

    // focus panel for accessibility
    const t = window.setTimeout(() => panelRef.current?.focus(), 0);

    function onKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape") onCancel();
      if (e.key === "Enter") onConfirm();
    }

    document.addEventListener("keydown", onKeyDown);
    return () => {
      window.clearTimeout(t);
      document.removeEventListener("keydown", onKeyDown);
    };
  }, [open, onCancel, onConfirm]);

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50"
      aria-modal="true"
      role="dialog"
      aria-labelledby="confirm-title"
      aria-describedby={description ? "confirm-desc" : undefined}
    >
      {/* Overlay */}
      <button
        className="absolute inset-0 bg-black/35"
        aria-label="Close"
        onClick={onCancel}
      />

      {/* Panel */}
      <div className="absolute inset-0 grid place-items-center p-4">
        <div
          ref={panelRef}
          tabIndex={-1}
          className="w-full max-w-md rounded-2xl bg-white p-4 shadow-xl ring-1 ring-zinc-200 outline-none"
        >
          <div className="space-y-1">
            <div id="confirm-title" className="text-base font-semibold text-zinc-900">
              {title}
            </div>
            {description && (
              <div id="confirm-desc" className="text-sm text-zinc-600">
                {description}
              </div>
            )}
          </div>

          <div className="mt-4 flex items-center justify-end gap-2">
            <button
              className="rounded-xl px-3 py-2 text-sm ring-1 ring-zinc-200 hover:bg-zinc-50"
              onClick={onCancel}
            >
              {cancelText}
            </button>

            <button
              className={[
                "rounded-xl px-3 py-2 text-sm font-medium text-white",
                variant === "danger"
                  ? "bg-red-600 hover:bg-red-700"
                  : "bg-zinc-900 hover:bg-zinc-800",
              ].join(" ")}
              onClick={onConfirm}
            >
              {confirmText}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
