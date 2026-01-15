// frontend/src/components/admin/QualificationCard/CardHeader.tsx
"use client";

import { Button } from "@/components/ui";
import type { QualificationMode } from "./types";

export default function CardHeader({
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
  return (
    <div className="flex items-start justify-between gap-4">
      <div>
        <div className="flex items-center gap-2">
          <div className="text-sm font-semibold text-zinc-900">{title}</div>

          {disabled ? (
            <span className="inline-flex items-center rounded-full bg-zinc-100 px-2 py-0.5 text-xs font-medium text-zinc-600">
              Enregistrement
            </span>
          ) : null}

          <span className="inline-flex items-center rounded-full bg-zinc-100 px-2 py-0.5 text-xs font-medium text-zinc-700">
            {count}
          </span>
        </div>

        <div className="mt-1 text-xs text-zinc-500">
          {mode === "agent" ? "Poste(s) qualifié(s) pour cet agent" : "Agent(s) qualifié(s) pour ce poste"}
        </div>
      </div>

      <Button type="button" variant="primary" size="compact" onClick={onToggleAdd} disabled={addDisabled}>
        + Ajouter
      </Button>
    </div>
  );
}
