"use client";

import * as React from "react";
import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";

export function PlanningPageHeader({
  titleSlot,
  subtitle,
  rightSlot,
  className,
}: {
  titleSlot: React.ReactNode;
  subtitle?: React.ReactNode;
  rightSlot?: React.ReactNode;
  className?: string;
}) {
  return (
    <Card className={cn("border border-border bg-card shadow-sm", className)}>
      <CardContent className="p-4 sm:p-5">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
          <div className="min-w-0">
            <div className="min-w-0">{titleSlot}</div>
            {subtitle ? (
              <div className="mt-1 text-sm text-muted-foreground">
                {subtitle}
              </div>
            ) : null}
          </div>

          {rightSlot ? <div className="shrink-0">{rightSlot}</div> : null}
        </div>
      </CardContent>
    </Card>
  );
}
