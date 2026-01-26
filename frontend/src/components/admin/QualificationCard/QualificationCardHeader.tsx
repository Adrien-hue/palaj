"use client";

import { Plus } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

import type { QualificationMode } from "./types";

export default function QualificationCardHeader({
  title,
  mode,
  count,
  disabled,
  addDisabled,
  onToggleAdd,
}: {
  title: string;
  mode: QualificationMode;
  count: number;
  disabled: boolean;
  addDisabled: boolean;
  onToggleAdd: () => void;
}) {
  const subtitle =
    mode === "agent"
      ? "Poste(s) qualifié(s) pour cet agent"
      : "Agent(s) qualifié(s) pour ce poste";

  return (
    <div className="flex items-start justify-between gap-4">
      <div className="min-w-0">
        <div className="flex flex-wrap items-center gap-2">
          <div className="truncate text-base font-semibold">{title}</div>

          {disabled ? (
            <Badge variant="secondary" className="gap-2">
              <span
                className="inline-flex h-2 w-2 rounded-full bg-amber-500 dark:bg-amber-400"
                aria-hidden="true"
              />
              Enregistrement
            </Badge>
          ) : null}

          <Badge variant="secondary">{count}</Badge>
        </div>

        <div className="mt-1 text-xs text-muted-foreground">{subtitle}</div>
      </div>

      <Button type="button" size="sm" onClick={onToggleAdd} disabled={addDisabled}>
        <Plus className="mr-2 h-4 w-4" />
        Ajouter
      </Button>
    </div>
  );
}
