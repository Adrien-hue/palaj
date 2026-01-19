"use client";

import type { InputHTMLAttributes } from "react";

type Props = Omit<InputHTMLAttributes<HTMLInputElement>, "onChange" | "value"> & {
  label: string;
  value: string;
  onChange: (next: string) => void;
  hint?: string;
  error?: string | null;
  allowFloat?: boolean;
  allowNegative?: boolean;
};

function isAllowedDraft(
  value: string,
  allowFloat: boolean,
  allowNegative: boolean
) {
  if (value === "") return true;

  // Regex autorisée
  // entier positif : \d*
  // float positif  : \d*(?:[.,]\d*)?
  const re = allowFloat
    ? allowNegative
      ? /^-?\d*(?:[.,]\d*)?$/
      : /^\d*(?:[.,]\d*)?$/
    : allowNegative
    ? /^-?\d*$/
    : /^\d*$/;

  return re.test(value);
}

export default function NumberField({
  label,
  value,
  onChange,
  hint,
  error,
  allowFloat = false,
  allowNegative = false,
  disabled,
  className = "",
  ...props
}: Props) {
  return (
    <label className={`text-xs text-zinc-700 ${className}`}>
      {label}

      <input
        {...props}
        inputMode={allowFloat ? "decimal" : "numeric"}
        className={[
          "mt-1 w-full rounded-lg border bg-white px-3 py-2 text-sm",
          error ? "border-red-300" : "border-zinc-200",
          disabled ? "opacity-60 cursor-not-allowed" : "",
        ].join(" ")}
        value={value}
        disabled={disabled}
        onKeyDown={(e) => {
          const allowedKeys = [
            "Backspace",
            "Delete",
            "ArrowLeft",
            "ArrowRight",
            "Home",
            "End",
            "Tab",
            "Enter",
          ];
          if (allowedKeys.includes(e.key)) return;
          if (e.ctrlKey || e.metaKey) return;

          // Block minus if negatives not allowed
          if (e.key === "-" && !allowNegative) {
            e.preventDefault();
            return;
          }

          // Block decimal if floats not allowed
          if ((e.key === "." || e.key === ",") && !allowFloat) {
            e.preventDefault();
            return;
          }

          const next = value + e.key;
          if (!isAllowedDraft(next, allowFloat, allowNegative)) {
            e.preventDefault();
          }
        }}
        onChange={(e) => {
          const raw = e.currentTarget.value;
          if (!isAllowedDraft(raw, allowFloat, allowNegative)) return;
          onChange(raw);
        }}
      />

      {hint && !error && (
        <div className="mt-1 text-[11px] text-zinc-500">{hint}</div>
      )}
      {error && (
        <div className="mt-1 text-[11px] text-red-600">{error}</div>
      )}
    </label>
  );
}
