// frontend/src/components/admin/QualificationCard/QualificationRow.tsx
"use client";

import { useEffect, useState } from "react";
import { Button, SecondaryButton } from "@/components/ui";
import { formatFR } from "./helpers";

export default function QualificationRow({
  label,
  dateYYYYMMDD,
  disabled,
  locked,
  isEditing,
  onStartEdit,
  onCancelEdit,
  onDelete,
  onSaveDate,
}: {
  label: string;
  dateYYYYMMDD: string;
  disabled?: boolean;
  locked?: boolean;
  isEditing?: boolean;
  onStartEdit: () => void;
  onCancelEdit: () => void;
  onDelete: () => void;
  onSaveDate: (dateYYYYMMDD: string) => Promise<void> | void;
}) {
  const [draft, setDraft] = useState(dateYYYYMMDD || "");

  useEffect(() => {
    setDraft(dateYYYYMMDD || "");
  }, [dateYYYYMMDD]);

  // Reset local draft when leaving edit mode
  useEffect(() => {
    if (!isEditing) setDraft(dateYYYYMMDD || "");
  }, [isEditing, dateYYYYMMDD]);

  const actionsDisabled = !!disabled || !!locked;
  const isDirty = draft !== (dateYYYYMMDD || "");
  const canSave = !!draft && isDirty;

  return (
    <div className="flex items-center justify-between gap-3 rounded-xl bg-zinc-50 px-3 py-2 ring-1 ring-zinc-100">
      <div className="min-w-0">
        <div className="truncate text-sm text-zinc-900">{label}</div>
      </div>

      <div className="flex items-center gap-2">
        {isEditing ? (
          <>
            <input
              type="date"
              className="rounded-lg border border-zinc-200 bg-white px-2 py-1 text-xs"
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              disabled={actionsDisabled}
            />

            <Button
              type="button"
              variant="successSoft"
              size="compact"
              onClick={async () => {
                await onSaveDate(draft);
              }}
              disabled={actionsDisabled || !canSave}
              title={!canSave ? "No changes to save" : "Save"}
            >
              OK
            </Button>

            <Button
              type="button"
              variant="dangerSoft"
              size="compact"
              onClick={() => {
                setDraft(dateYYYYMMDD || "");
                onCancelEdit();
              }}
              disabled={actionsDisabled}
            >
              Annuler
            </Button>
          </>
        ) : (
          <>
            <div className="text-xs text-zinc-600">{formatFR(dateYYYYMMDD)}</div>

            <SecondaryButton type="button" size="compact" onClick={onStartEdit} disabled={actionsDisabled}>
              Modifier
            </SecondaryButton>
          </>
        )}

        <Button type="button" variant="dangerSoft" size="compact" onClick={onDelete} disabled={actionsDisabled}>
          Supprimer
        </Button>
      </div>
    </div>
  );
}
