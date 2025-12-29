"use client";

import type { ReactNode, SelectHTMLAttributes } from "react";

export type SelectOption = {
  value: string;
  label: string;
  disabled?: boolean;
};

export default function SelectField({
  label,
  options,
  hint,
  error,
  mandatory = false,
  placeholder,
  className = "",
  selectClassName = "",
  rightSlot,
  ...props
}: SelectHTMLAttributes<HTMLSelectElement> & {
  label: string;
  options: SelectOption[];
  hint?: string;
  error?: string | null;
  mandatory?: boolean;
  placeholder?: string; // ex "Sélectionner..."
  className?: string;
  selectClassName?: string;
  rightSlot?: ReactNode;
}) {
    const border = error ? "border-red-300" : "border-zinc-200";
    const ring = error ? "focus:ring-red-200" : "focus:ring-zinc-300";
  
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

        <div className="relative">
            <select
            {...props}
            required={mandatory || props.required}
            className={[
                "w-full rounded-xl border bg-white px-3 py-2 pr-10 text-sm outline-none transition",
                "appearance-none",
                border,
                `focus:ring-2 ${ring}`,
                "disabled:opacity-60 disabled:cursor-not-allowed",
                selectClassName,
            ].join(" ")}
            >
            {placeholder !== undefined && (
                <option value="" disabled={mandatory}>
                {placeholder}
                </option>
            )}

            {options.map((o) => (
                <option key={o.value} value={o.value} disabled={o.disabled}>
                {o.label}
                </option>
            ))}
            </select>

            {/* Chevron */}
            <div className="pointer-events-none absolute inset-y-0 right-3 flex items-center text-zinc-500">
            <svg width="16" height="16" viewBox="0 0 24 24" aria-hidden="true">
                <path
                fill="currentColor"
                d="M7 10l5 5l5-5"
                />
            </svg>
            </div>
        </div>

        {error ? (
            <div className="text-xs text-red-700">{error}</div>
        ) : hint ? (
            <div className="text-xs text-zinc-500">{hint}</div>
        ) : null}
        </label>
    );
}
