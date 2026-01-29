"use client";

import * as React from "react";
import { Separator } from "@/components/ui/separator";
import { Card } from "@/components/ui/card";
import { cn } from "@/lib/utils";

export type DrawerSectionVariant = "card" | "surface";

export function DrawerSection({
  title,
  subtitle,
  right,
  variant = "surface",
  className,
  children,
}: {
  title: React.ReactNode;
  subtitle?: React.ReactNode;
  right?: React.ReactNode;
  variant?: DrawerSectionVariant;
  className?: string;
  children: React.ReactNode;
}) {
  const header = (
    <>
      <div className="flex items-center justify-between gap-2">
        <div className={cn("text-sm font-semibold", variant === "card" && "font-medium")}>
          {title}
        </div>
        {right ? <div className="shrink-0">{right}</div> : null}
      </div>

      {subtitle ? (
        <div className="mt-1 text-xs text-muted-foreground">{subtitle}</div>
      ) : null}

      <Separator className="my-3" />
    </>
  );

  if (variant === "card") {
    return (
      <Card className={cn("p-4", className)}>
        {header}
        {children}
      </Card>
    );
  }

  // surface (ton style app surface/bg/border)
  return (
    <div
      className={cn(
        "rounded-xl border border-border bg-card p-3",
        className
      )}
    >
      {header}
      {children}
    </div>
  );
}

export function EmptyBox({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "rounded-xl border border-dashed border-[color:var(--app-border)] p-4 text-sm text-[color:var(--app-muted)]",
        className
      )}
    >
      {children}
    </div>
  );
}
