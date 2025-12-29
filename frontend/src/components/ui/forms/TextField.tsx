"use client";

import type { InputHTMLAttributes, ReactNode } from "react";

export default function TextField({
  label,
  hint,
  error,
  rightSlot,
  mandatory = false,
  className = "",
  inputClassName = "",
  ...props
}: InputHTMLAttributes<HTMLInputElement> & {
  label: string;
  hint?: string;
  error?: string | null;
  rightSlot?: ReactNode;
  mandatory?: boolean;
  className?: string;
  inputClassName?: string;
}) {
  return (
    <label className={`block space-y-1 ${className}`}>
      <div className="flex items-center justify-between gap-3">
        <div className="text-xs font-medium text-zinc-700">
          {label}
          {mandatory && (
            <span className="ml-1 text-red-600" aria-hidden="true">
              *
            </span>
          )}
        </div>
        {rightSlot}
      </div>

      <input
        {...props}
        required={mandatory || props.required}
        className={[
          "w-full rounded-xl border px-3 py-2 text-sm outline-none transition",
          error
            ? "border-red-300 focus:ring-2 focus:ring-red-200"
            : "border-zinc-200 focus:ring-2 focus:ring-zinc-300",
          "disabled:opacity-60 disabled:cursor-not-allowed",
          inputClassName,
        ].join(" ")}
      />

      {error ? (
        <div className="text-xs text-red-700">{error}</div>
      ) : hint ? (
        <div className="text-xs text-zinc-500">{hint}</div>
      ) : null}
    </label>
  );
}
