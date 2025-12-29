"use client";

import type { ButtonHTMLAttributes } from "react";

export default function SecondaryButton({
  children,
  className = "",
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement>) {
  return (
    <button
      {...props}
      className={`inline-flex items-center justify-center rounded-xl px-4 py-2 text-sm ring-1 ring-zinc-200 hover:bg-zinc-50 transition focus:outline-none focus-visible:ring-2 focus-visible:ring-zinc-300 disabled:opacity-60 disabled:cursor-not-allowed ${className}`}
    >
      {children}
    </button>
  );
}
