"use client";

import * as React from "react";
import { Badge } from "@/components/ui/badge";
import { RhSeverityBadge, type RhSeverity } from "./RhSeverityBadge";

export function RhViolationCard({
  severity,
  title,
  message,
  rangeLabel,
  count,
}: {
  severity: RhSeverity;
  title: string;
  message: string;
  rangeLabel?: string | null;
  count?: number;
}) {
  return (
    <div className="rounded border bg-muted p-2">
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2 min-w-0">
          <RhSeverityBadge severity={severity} />
          <div className="truncate text-[11px] text-muted-foreground">
            {title}
          </div>
        </div>

        {typeof count === "number" && count > 1 ? (
          <Badge
            variant="outline"
            className="h-5 rounded-full px-2 py-0 text-[10px]"
          >
            x{count}
          </Badge>
        ) : null}
      </div>

      <div className="mt-1 text-sm">{message}</div>

      {rangeLabel ? (
        <div className="mt-1 text-[11px] text-muted-foreground">
          {rangeLabel}
        </div>
      ) : null}
    </div>
  );
}
