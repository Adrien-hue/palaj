"use client";

import { useEffect, useId, useRef } from "react";

export type DialogProps = {
  open: boolean;
  title: string;
  children: React.ReactNode;

  onClose: () => void;

  /** Fixed footer area (actions). Prefer putting primary actions here. */
  footer?: React.ReactNode;

  /** Max width utility class (Tailwind). */
  maxWidthClassName?: string;

  /** Panel max height in viewport. Default: 90vh. */
  maxHeightClassName?: string;

  /** Close when clicking on the backdrop overlay. Default: true. */
  closeOnBackdrop?: boolean;

  /** Close when pressing Escape. Default: true. */
  closeOnEscape?: boolean;

  /** Prevent body scroll when dialog is open. Default: true. */
  lockScroll?: boolean;

  /** Optional subtitle / helper text displayed under the title. */
  description?: string;
};

export default function Dialog({
  open,
  title,
  description,
  children,
  onClose,
  footer,
  maxWidthClassName = "max-w-lg",
  maxHeightClassName = "max-h-[90vh]",
  closeOnBackdrop = true,
  closeOnEscape = true,
  lockScroll = true,
}: DialogProps) {
  const panelRef = useRef<HTMLDivElement | null>(null);
  const titleId = useId();
  const descId = useId();

  // Focus management + Escape handling
  useEffect(() => {
    if (!open) return;

    const t = window.setTimeout(() => panelRef.current?.focus(), 0);

    function onKeyDown(e: KeyboardEvent) {
      if (!closeOnEscape) return;
      if (e.key === "Escape") onClose();
    }

    document.addEventListener("keydown", onKeyDown);
    return () => {
      window.clearTimeout(t);
      document.removeEventListener("keydown", onKeyDown);
    };
  }, [open, onClose, closeOnEscape]);

  // Lock body scroll while open (prevents the page behind from scrolling)
  useEffect(() => {
    if (!open || !lockScroll) return;

    const prevOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";

    return () => {
      document.body.style.overflow = prevOverflow;
    };
  }, [open, lockScroll]);

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-[70]"
      role="dialog"
      aria-modal="true"
      aria-labelledby={titleId}
      aria-describedby={description ? descId : undefined}
    >
      {/* Backdrop */}
      <button
        type="button"
        className="absolute inset-0 bg-black/35"
        aria-label="Close dialog"
        onClick={closeOnBackdrop ? onClose : undefined}
      />

      <div className="absolute inset-0 grid place-items-center p-4">
        <div
          ref={panelRef}
          tabIndex={-1}
          className={[
            "w-full overflow-hidden rounded-2xl bg-white shadow-xl ring-1 ring-zinc-200 outline-none",
            "flex flex-col",
            maxWidthClassName,
            maxHeightClassName,
          ].join(" ")}
        >
          {/* Header (fixed) */}
          <div className="flex items-start justify-between gap-3 border-b border-zinc-100 px-4 py-3">
            <div className="min-w-0">
              <div id={titleId} className="truncate text-sm font-semibold text-zinc-900">
                {title}
              </div>
              {description ? (
                <div id={descId} className="mt-0.5 text-xs text-zinc-500">
                  {description}
                </div>
              ) : null}
            </div>

            <button
              type="button"
              className="shrink-0 rounded-lg px-2 py-1 text-sm text-zinc-500 hover:bg-zinc-100 focus:outline-none focus-visible:ring-2 focus-visible:ring-zinc-300"
              onClick={onClose}
              aria-label="Close dialog"
              title="Close"
            >
              ✕
            </button>
          </div>

          {/* Body (scrollable) */}
          <div className="dialog-scroll flex-1 overflow-y-auto px-4 py-4">
            {children}
          </div>

          {/* Footer (fixed) */}
          {footer ? (
            <div className="border-t border-zinc-100 px-4 py-3">{footer}</div>
          ) : null}
        </div>
      </div>
    </div>
  );
}
