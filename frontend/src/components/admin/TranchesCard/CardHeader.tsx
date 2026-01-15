// frontend/src/components/admin/TranchesCard/CardHeader.tsx
"use client";

import { Button, SecondaryButton } from "@/components/ui";

export default function CardHeader({
  title,
  count,
  disabled,
  addDisabled,
  onToggleAdd,
  listOpen,
  onToggleList,
}: {
  title: string;
  count: number;
  disabled: boolean;
  addDisabled: boolean;
  onToggleAdd: () => void;
  listOpen: boolean;
  onToggleList: () => void;
}) {
  return (
    <div className="flex items-start justify-between gap-4">
      <div>
        <div className="flex items-center gap-2">
          <div className="text-sm font-semibold text-zinc-900">{title}</div>

          {disabled ? (
            <span className="inline-flex items-center rounded-full bg-zinc-100 px-2 py-0.5 text-xs font-medium text-zinc-600">
              Enregistrement...
            </span>
          ) : null}

          <span className="inline-flex items-center rounded-full bg-zinc-100 px-2 py-0.5 text-xs font-medium text-zinc-700">
            {count}
          </span>
        </div>

        <div className="mt-1 text-xs text-zinc-500">Tranches relatives à ce poste.</div>
      </div>

      <div className="flex items-center gap-2">
        <SecondaryButton
          type="button"
          size="compact"
          onClick={onToggleList}
          disabled={disabled}
        >
          {listOpen ? "Masquer la liste" : "Afficher la liste"}
        </SecondaryButton>
        
        <Button type="button" variant="primary" size="compact" onClick={onToggleAdd} disabled={addDisabled}>
          + Ajouter
        </Button>
      </div>
    </div>
  );
}
