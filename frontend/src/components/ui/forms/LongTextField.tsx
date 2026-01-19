"use client";

import type { TextareaHTMLAttributes } from "react";
import FormError from "./FormError";

export default function LongTextField({
  label,
  value,
  onChange,
  error,
  helperText,
  required,
  rows = 4,
  className = "",
  ...props
}: Omit<TextareaHTMLAttributes<HTMLTextAreaElement>, "value" | "onChange"> & {
  label: string;
  value: string;
  onChange: (v: string) => void;
  error?: string | null;
  helperText?: string;
  required?: boolean;
  rows?: number;
}) {
  return (
    <label className={`block text-xs text-zinc-700 ${className}`}>
      <div className="flex items-center gap-1">
        <span>{label}</span>
        {required ? <span className="text-red-600">*</span> : null}
      </div>

      <textarea
        {...props}
        rows={rows}
        className={[
          "mt-1 w-full rounded-lg border bg-white px-3 py-2 text-sm",
          error ? "border-red-300" : "border-zinc-200",
          "focus:outline-none focus-visible:ring-2 focus-visible:ring-zinc-300",
          "disabled:opacity-60 disabled:cursor-not-allowed",
        ].join(" ")}
        value={value}
        onChange={(e) => onChange(e.target.value)}
      />

      {helperText ? <div className="mt-1 text-[11px] text-zinc-500">{helperText}</div> : null}
      {error ? <FormError message={error} /> : null}
    </label>
  );
}
