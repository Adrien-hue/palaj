"use client";

import * as React from "react";
import { cn } from "@/lib/utils";

type OnSelect = (e: React.MouseEvent<HTMLButtonElement>) => void;

export function PlanningDayCellFrame({
  onSelect,
  ariaLabel,
  pressed,
  disabled = false,

  isOutsideMonth = false,
  isOutsideRange = false,
  isInSelectedWeek = false,

  multiSelected = false,

  className,
  children,
}: {
  onSelect: OnSelect | (() => void);
  ariaLabel: string;
  pressed: boolean;
  disabled?: boolean;

  isOutsideMonth?: boolean;
  isOutsideRange?: boolean;
  isInSelectedWeek?: boolean;

  multiSelected?: boolean;

  className?: string;
  children: React.ReactNode;
}) {
  const isDisabled = disabled || isOutsideRange;

  const handleClick = React.useCallback(
    (e: React.MouseEvent<HTMLButtonElement>) => {
      (onSelect as OnSelect)(e);
    },
    [onSelect],
  );

  return (
    <button
      type="button"
      onClick={handleClick}
      aria-label={ariaLabel}
      aria-pressed={pressed}
      aria-disabled={isDisabled ? "true" : undefined}
      disabled={isDisabled}
      data-selected={pressed ? "true" : undefined}
      data-multi-selected={multiSelected ? "true" : undefined}
      data-week={isInSelectedWeek ? "true" : undefined}
      data-outside-month={isOutsideMonth ? "true" : undefined}
      data-outside-range={isOutsideRange ? "true" : undefined}
      className={cn(
        // base
        "w-full rounded-xl border p-2 text-left min-h-[92px]",
        "bg-card text-card-foreground border-border",
        "transition-colors transition-shadow duration-150",
        "focus:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-card",

        // hover / motion (disabled when outside range)
        !isDisabled && "hover:bg-muted/40 hover:-translate-y-[1px] hover:shadow-sm",

        // outside
        (isOutsideMonth || isOutsideRange) && "opacity-60",

        // week highlight (only when not pressed/multi)
        !pressed && !multiSelected && isInSelectedWeek && "border-muted-foreground/30",

        // pressed (grid focus/selection)
        pressed && !multiSelected && "ring-1 ring-ring",

        // multi-selected (dominant visual state)
        multiSelected &&
          "border-primary/70 bg-primary/15 ring-2 ring-primary shadow-sm",

        className,
      )}
    >
      {children}
    </button>
  );
}
