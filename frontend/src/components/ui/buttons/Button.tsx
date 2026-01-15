"use client";

import type { ButtonHTMLAttributes } from "react";

export default function Button({
  children,
  loading,
  variant = "primary",
  size = "default",
  className = "",
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & {
  loading?: boolean;
  variant?: "primary" | "danger" | "dangerSoft" | "success" | "successSoft";
  size?: "default" | "compact";
}) {
  const base =
    "inline-flex items-center justify-center cursor-pointer transition active:scale-[0.99] " +
    "focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 " +
    "disabled:opacity-60 disabled:cursor-not-allowed disabled:active:scale-100";

  const sizes = {
    default: "rounded-xl px-4 py-2 text-sm font-medium",
    compact: "rounded-lg px-2 py-1 text-xs font-medium",
  } as const;

  const variants = {
    primary:
      "border-2 border-transparent bg-zinc-900 text-white hover:bg-zinc-800 focus-visible:ring-zinc-400",

    danger:
      "border-2 border-transparent bg-red-600 text-white hover:bg-red-700 focus-visible:ring-red-500",

    dangerSoft:
      "border-2 border-red-300 bg-red-100 text-red-700 hover:bg-red-600 hover:text-white focus-visible:ring-red-400",

    success:
      "border-2 border-transparent bg-green-600 text-white hover:bg-green-700 focus-visible:ring-green-500",

    successSoft:
      "border-2 border-green-300 bg-green-100 text-green-700 hover:bg-green-600 hover:text-white focus-visible:ring-green-400",
  } as const;

  return (
    <button
      {...props}
      disabled={props.disabled || loading}
      className={`${base} ${sizes[size]} ${variants[variant]} ${className}`}
    >
      {loading ? "…" : children}
    </button>
  );
}
