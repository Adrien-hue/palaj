"use client";

import type { ReactNode } from "react";
import { Badge } from "@/components/ui/badge";
import { RhSeverityBadge, type RhSeverity } from "./RhSeverityBadge";

export type RhViolationCardProps = {
  severity: RhSeverity;
  title: string;
  message: string;
  rangeLabel?: string | null;
  count?: number;
  contextSlot?: ReactNode;
  actionsSlot?: ReactNode;
};

export function RhViolationCard({
  severity,
  title,
  message,
  rangeLabel,
  count,
  contextSlot,
  actionsSlot,
}: RhViolationCardProps) {
  const showCount = typeof count === "number" && count > 1;

  return (
    <div className="rounded-xl border bg-card p-3 shadow-sm transition-colors hover:bg-muted/40">
      {/* Header */}
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <RhSeverityBadge severity={severity} />
            <div className="truncate text-sm font-medium leading-5" title={title}>
              {title || "Violation"}
            </div>
          </div>

          {/* Meta (2 lignes) */}
          <div className="mt-1 space-y-1 text-[12px] text-muted-foreground">
            {contextSlot ? (
              <div className="flex items-center gap-2 min-w-0">{contextSlot}</div>
            ) : null}

            {rangeLabel ? (
              <div className="truncate" title={rangeLabel}>
                {rangeLabel}
              </div>
            ) : null}
          </div>
        </div>

        {showCount ? (
          <Badge variant="outline" className="h-6 rounded-full px-2 py-0 text-[11px] tabular-nums">
            x{count}
          </Badge>
        ) : null}
      </div>

      {/* Message */}
      <div className="mt-3 rounded-lg bg-muted/50 px-3 py-2 text-sm leading-5">
        {message}
      </div>

      {/* Actions */}
      {actionsSlot ? (
        <div className="mt-2 flex flex-wrap items-center gap-2">
          {actionsSlot}
        </div>
      ) : null}
    </div>
  );
}
