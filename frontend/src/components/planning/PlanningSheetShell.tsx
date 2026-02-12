"use client";

import * as React from "react";
import { X } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Sheet,
  SheetClose,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
  SheetFooter,
} from "@/components/ui/sheet";
import { cn } from "@/lib/utils";

const DEFAULT_SHEET_WIDTH = "w-full sm:w-[520px]";

type HeaderVariant = "normal" | "sticky";

export type PlanningSheetShellProps = {
  open: boolean;
  onOpenChange: (open: boolean) => void;

  /** Ex: "w-[420px] sm:w-[520px]" ou "w-full sm:max-w-lg" */
  contentClassName?: string;

  /** Wrapper global (souvent h-full + bg) */
  rootClassName?: string;

  /** Zone content padding (ex: p-6 ou p-4) */
  bodyClassName?: string;

  headerVariant?: HeaderVariant;

  title: React.ReactNode;
  description?: React.ReactNode;

  /** Pour mettre un vrai empty state dans le shell si tu veux */
  isEmpty?: boolean;
  empty?: React.ReactNode;

  children?: React.ReactNode;

  footer?: React.ReactNode;
  footerClassName?: string;
};

export function PlanningSheetShell({
  open,
  onOpenChange,
  contentClassName,
  rootClassName,
  bodyClassName,
  headerVariant = "normal",
  title,
  description,
  isEmpty,
  empty,
  children,
  footer,
  footerClassName,
}: PlanningSheetShellProps) {
  const headerInner = (
    <SheetHeader className="space-y-2">
      <div className="flex items-start gap-3">
        <div className="min-w-0 flex-1">
          <SheetTitle>{title}</SheetTitle>
          {description ? (
            typeof description === "string" ? (
              <SheetDescription>{description}</SheetDescription>
            ) : (
              <div className="space-y-2 text-sm text-muted-foreground">
                {description}
              </div>
            )
          ) : null}
        </div>

        <SheetClose asChild>
          <Button
            variant="ghost"
            size="icon"
            className="shrink-0"
            aria-label="Fermer"
          >
            <X className="h-4 w-4" />
          </Button>
        </SheetClose>
      </div>
    </SheetHeader>
  );

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent
        className={cn("p-0", contentClassName ?? DEFAULT_SHEET_WIDTH)}
      >
        <div className={cn("h-full flex flex-col", rootClassName)}>
          {headerVariant === "sticky" ? (
            <div className="sticky top-0 z-10 border-b border-border bg-background/95 backdrop-blur p-4">
              {headerInner}
            </div>
          ) : (
            <div className={cn("p-6", bodyClassName)}>{headerInner}</div>
          )}

          {/* Body */}
          <div
            className={cn(
              "flex-1 overflow-auto",
              headerVariant === "sticky" ? bodyClassName : "px-6 pb-6",
            )}
          >
            {isEmpty ? empty : children}
          </div>

          {footer ? (
            <div
              className={cn(
                "sticky bottom-0 z-10 border-t border-border bg-background/95 backdrop-blur p-4",
                footerClassName,
              )}
            >
              <SheetFooter>{footer}</SheetFooter>
            </div>
          ) : null}
        </div>
      </SheetContent>
    </Sheet>
  );
}

export function PlanningSheetCloseButton({
  children,
}: {
  children: React.ReactNode;
}) {
  return <SheetClose asChild>{children}</SheetClose>;
}
