"use client";

import * as React from "react";
import { Badge } from "@/components/ui/badge";

export type RhSeverity = "error" | "warning" | "info";

export function RhSeverityBadge({
  severity,
  compact = true,
}: {
  severity: RhSeverity;
  compact?: boolean;
}) {
  const variant =
    severity === "error"
      ? "destructive"
      : severity === "warning"
        ? "secondary"
        : "outline";

  const label =
    severity === "error"
      ? "BLOQUANT"
      : severity === "warning"
        ? "ALERTE"
        : "INFO";

  return (
    <Badge
      variant={variant}
      className={compact ? "h-5 rounded-full px-2 py-0 text-[10px]" : undefined}
    >
      {label}
    </Badge>
  );
}
