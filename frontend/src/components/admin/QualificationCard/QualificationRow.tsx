"use client";

import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";

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
    <div
      className={cn(
        "flex items-center justify-between gap-3 rounded-xl border bg-muted/30 px-3 py-2",
        actionsDisabled && "opacity-80"
      )}
    >
      <div className="min-w-0">
        <div className="truncate text-sm font-medium text-foreground">{label}</div>
      </div>

      <div className="flex items-center gap-2">
        {isEditing ? (
          <>
            <Input
              type="date"
              className="h-8 w-[160px] text-xs"
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              disabled={actionsDisabled}
            />

            <Button
              type="button"
              size="sm"
              onClick={async () => {
                await onSaveDate(draft);
              }}
              disabled={actionsDisabled || !canSave}
              title={!canSave ? "Aucun changement à enregistrer" : "Enregistrer"}
            >
              OK
            </Button>

            <Button
              type="button"
              variant="outline"
              size="sm"
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
            <div className="text-xs text-muted-foreground whitespace-nowrap">
              {formatFR(dateYYYYMMDD)}
            </div>

            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={onStartEdit}
              disabled={actionsDisabled}
            >
              Modifier
            </Button>
          </>
        )}

        <Button
          type="button"
          variant="destructive"
          size="sm"
          onClick={onDelete}
          disabled={actionsDisabled}
        >
          Supprimer
        </Button>
      </div>
    </div>
  );
}
