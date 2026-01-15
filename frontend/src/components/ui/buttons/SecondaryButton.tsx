"use client";

import type { ButtonHTMLAttributes } from "react";

type Props = ButtonHTMLAttributes<HTMLButtonElement> & {
  size?: "default" | "compact";
};

export default function SecondaryButton({
  children,
  size = "default",
  className = "",
  ...props
}: Props) {
  // Base comportement bouton
  const base =
    "inline-flex items-center justify-center select-none cursor-pointer transition " +
    "focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 " +
    "disabled:opacity-60 disabled:cursor-not-allowed disabled:active:scale-100";

  // Tailles
  const sizes = {
    default: "h-10 rounded-xl px-4 text-sm",
  compact: "h-8 rounded-lg px-2 text-xs",
  } as const;

  // Style visuel “secondary”
  const appearance =
    "bg-white text-zinc-900 ring-1 ring-zinc-200 shadow-sm";

  // Hover / active feedback
  const interaction =
    "hover:bg-zinc-50 hover:ring-zinc-300 hover:shadow " +
    "active:bg-zinc-100 active:scale-[0.99]";

  // Focus
  const focus =
    "focus-visible:ring-zinc-300";

  // Disabled overrides
  const disabled =
    "disabled:hover:bg-white disabled:hover:shadow-sm";

  return (
    <button
      {...props}
      className={[
        base,
        sizes[size],
        appearance,
        interaction,
        focus,
        disabled,
        className,
      ].join(" ")}
    >
      {children}
    </button>
  );
}
