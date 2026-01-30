"use client";

import * as React from "react";
import { cn } from "@/lib/utils";

export function PlanningDayCellFrame({
  onSelect,
  ariaLabel,
  pressed,
  disabled = false,

  isOutsideMonth = false,
  isOutsideRange = false,
  isInSelectedWeek = false,

  className,
  children,
}: {
  onSelect: () => void;
  ariaLabel: string;
  pressed: boolean;
  disabled?: boolean;

  isOutsideMonth?: boolean;
  isOutsideRange?: boolean;
  isInSelectedWeek?: boolean;

  className?: string;
  children: React.ReactNode;
}) {
  const isDisabled = disabled || isOutsideRange;

  return (
    <button
      type="button"
      onClick={onSelect}
      aria-label={ariaLabel}
      aria-pressed={pressed}
      aria-disabled={isDisabled ? "true" : undefined}
      disabled={isDisabled}
      data-selected={pressed ? "" : undefined}
      data-week={isInSelectedWeek ? "" : undefined}
      data-outside-month={isOutsideMonth ? "" : undefined}
      data-outside-range={isOutsideRange ? "" : undefined}
      className={cn(
        // base
        "w-full rounded-xl border p-2 text-left transition",
        "bg-card text-card-foreground border-border",
        "hover:bg-muted/40",
        "focus:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background",
        "hover:-translate-y-[1px] hover:shadow-sm",
        // ✅ stable height (reduces layout shift)
        "min-h-[92px]",
        // states
        pressed && "ring-2 ring-ring",
        !pressed && isInSelectedWeek && "ring-1 ring-border",
        (isOutsideMonth || isOutsideRange) && "opacity-60",
        isOutsideRange && "pointer-events-none",
        className
      )}
    >
      {children}
    </button>
  );
}
