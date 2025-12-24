"use client";

import React, {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
} from "react";

export type ToastType = "success" | "error" | "info";

export type Toast = {
  id: string;
  type: ToastType;
  title: string;
  message?: string;
  durationMs?: number;
};

type ToastContextValue = {
  showToast: (t: Omit<Toast, "id">) => void;
  dismissToast: (id: string) => void;
};

const ToastContext = createContext<ToastContextValue | null>(null);

function uid() {
  return Math.random().toString(36).slice(2) + Date.now().toString(36);
}

function styles(type: ToastType) {
  switch (type) {
    case "success":
      return "border-green-200 bg-white";
    case "error":
      return "border-red-200 bg-white";
    case "info":
    default:
      return "border-zinc-200 bg-white";
  }
}

function badge(type: ToastType) {
  switch (type) {
    case "success":
      return "bg-green-100 text-green-700";
    case "error":
      return "bg-red-100 text-red-700";
    case "info":
    default:
      return "bg-zinc-100 text-zinc-700";
  }
}

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const dismissToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const showToast = useCallback(
    (t: Omit<Toast, "id">) => {
      const id = uid();
      const duration = t.durationMs ?? 3500;

      const toast: Toast = { id, ...t, durationMs: duration };
      setToasts((prev) => [toast, ...prev].slice(0, 5)); // max 5

      window.setTimeout(() => dismissToast(id), duration);
    },
    [dismissToast]
  );

  const value = useMemo(
    () => ({ showToast, dismissToast }),
    [showToast, dismissToast]
  );

  return (
    <ToastContext.Provider value={value}>
      {children}

      {/* Toaster */}
      <div
        className="fixed right-4 top-16 z-[60] flex w-[360px] max-w-[calc(100vw-2rem)] flex-col gap-2"
        aria-live="polite"
        aria-relevant="additions"
      >
        {toasts.map((t) => (
          <div
            key={t.id}
            className={[
              "rounded-2xl border p-3 shadow-sm",
              styles(t.type),
            ].join(" ")}
          >
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0">
                <div className="flex items-center gap-2">
                  <span
                    className={[
                      "rounded-full px-2 py-0.5 text-xs font-medium",
                      badge(t.type),
                    ].join(" ")}
                  >
                    {t.type === "success"
                      ? "Succès"
                      : t.type === "error"
                      ? "Erreur"
                      : "Info"}
                  </span>
                  <div className="truncate text-sm font-semibold text-zinc-900">
                    {t.title}
                  </div>
                </div>
                {t.message && (
                  <div className="mt-1 text-sm text-zinc-600">{t.message}</div>
                )}
              </div>

              <button
                className="shrink-0 rounded-lg px-2 py-1 text-sm text-zinc-500 hover:bg-zinc-100"
                onClick={() => dismissToast(t.id)}
                aria-label="Fermer"
                title="Fermer"
              >
                ✕
              </button>
            </div>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error("useToast must be used within ToastProvider");
  return ctx;
}
