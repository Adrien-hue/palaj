"use client";

import type { ButtonHTMLAttributes } from "react";

export default function Button({
  children,
  loading,
  variant = "primary",
  className = "",
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & {
  loading?: boolean;
  variant?: "primary" | "danger" | "success";
}) {
  const base =
    "inline-flex items-center justify-center rounded-xl px-4 py-2 text-sm font-medium transition focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 disabled:opacity-60 disabled:cursor-not-allowed";

  const variants = {
    primary:
      "bg-zinc-900 text-white hover:bg-zinc-800 focus-visible:ring-zinc-400",
    danger:
      "bg-red-600 text-white hover:bg-red-700 focus-visible:ring-red-500",
    success:
      "bg-green-600 text-white hover:bg-green-700 focus-visible:ring-green-500",
  };

  return (
    <button
      {...props}
      disabled={props.disabled || loading}
      className={`${base} ${variants[variant]} ${className}`}
    >
      {loading ? "…" : children}
    </button>
  );
}
