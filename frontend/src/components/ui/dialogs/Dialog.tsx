"use client";

import { useEffect, useRef } from "react";

export default function Dialog({
  open,
  title,
  children,
  onClose,
  footer,
  maxWidthClassName = "max-w-lg",
}: {
  open: boolean;
  title: string;
  children: React.ReactNode;
  onClose: () => void;
  footer?: React.ReactNode;
  maxWidthClassName?: string;
}) {
  const panelRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!open) return;

    const t = window.setTimeout(() => panelRef.current?.focus(), 0);
    function onKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape") onClose();
    }
    document.addEventListener("keydown", onKeyDown);
    return () => {
      window.clearTimeout(t);
      document.removeEventListener("keydown", onKeyDown);
    };
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-[70]" role="dialog" aria-modal="true">
      <button
        className="absolute inset-0 bg-black/35"
        aria-label="Fermer"
        onClick={onClose}
      />
      <div className="absolute inset-0 grid place-items-center p-4">
        <div
          ref={panelRef}
          tabIndex={-1}
          className={[
            "w-full rounded-2xl bg-white shadow-xl ring-1 ring-zinc-200 outline-none",
            maxWidthClassName,
          ].join(" ")}
        >
          <div className="flex items-center justify-between gap-3 border-b border-zinc-100 px-4 py-3">
            <div className="text-sm font-semibold text-zinc-900">{title}</div>
            <button
              className="rounded-lg px-2 py-1 text-sm text-zinc-500 hover:bg-zinc-100"
              onClick={onClose}
              aria-label="Fermer"
              title="Fermer"
            >
              ✕
            </button>
          </div>

          <div className="px-4 py-4">{children}</div>

          {footer && (
            <div className="border-t border-zinc-100 px-4 py-3">{footer}</div>
          )}
        </div>
      </div>
    </div>
  );
}
