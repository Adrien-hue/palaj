"use client";

import type * as React from "react";
import { cn } from "@/lib/utils";

export function AdminDetailsRow({
  label,
  value,
  className,
  bordered = true,
}: {
  label: string;
  value: React.ReactNode;
  className?: string;
  bordered?: boolean;
}) {
  return (
    <div
      className={cn(
        "grid grid-cols-[minmax(0,1fr)_minmax(0,1fr)] items-start gap-4 py-2",
        bordered && "border-b border-border/60 last:border-b-0",
        className
      )}
    >
      <div className="text-xs font-medium text-muted-foreground">{label}</div>

      <div className="text-sm font-medium text-foreground text-right break-words">
        {value}
      </div>
    </div>
  );
}
