"use client";

import * as React from "react";
import { cn } from "@/lib/utils";

type OnSelect = (e: React.MouseEvent<HTMLButtonElement>) => void;

type Tone = "none" | "info" | "warning" | "danger";

export function PlanningDayCellFrame({
  onSelect,
  ariaLabel,
  pressed,
  disabled = false,

  isOutsideMonth = false,
  isOutsideRange = false,
  isInSelectedWeek = false,

  multiSelected = false,

  tone = "none",
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

  tone?: Tone;
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

  const toneBg =
    tone === "danger"
      ? "bg-destructive/10 hover:bg-destructive/15 border-destructive/35"
      : tone === "warning"
        ? "bg-amber-500/10 hover:bg-amber-500/15 border-amber-500/30"
        : tone === "info"
          ? "bg-muted/15 hover:bg-muted/20"
          : "";


  // Selection styling:
  // - pressed adds ring but keeps tone background
  // - multiSelected stays dominant
  const pressedClass = pressed && !multiSelected ? "ring-1 ring-ring" : "";

  const multiSelectedClass =
    multiSelected && "border-primary/70 ring-2 ring-primary shadow-sm";

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
        !isDisabled && "hover:-translate-y-[1px] hover:shadow-sm",

        // tone (overrides default hover bg)
        !isDisabled && toneBg,
        // default hover bg only if no tone
        !isDisabled && tone === "none" && "hover:bg-muted/40",

        // outside
        (isOutsideMonth || isOutsideRange) && "opacity-60",

        // week highlight (only when not pressed/multi)
        !pressed && !multiSelected && isInSelectedWeek && "border-muted-foreground/30",

        // pressed / multi
        pressedClass,
        multiSelectedClass,

        className,
      )}
    >
      {children}
    </button>
  );
}
