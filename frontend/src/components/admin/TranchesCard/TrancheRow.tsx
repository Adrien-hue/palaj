"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { Button, SecondaryButton } from "@/components/ui";
import type { TrancheDraft } from "./types";
import { formatRange, isValidTimeHHMM } from "./helpers";

export type TrancheRowProps = {
  id: number;
  label: string;
  heure_debut: string; // "HH:MM"
  heure_fin: string; // "HH:MM"

  disabled?: boolean;
  locked?: boolean;
  isEditing?: boolean;

  onStartEdit: () => void;
  onCancelEdit: () => void;
  onDelete: () => void;
  onSave: (draft: TrancheDraft) => Promise<void> | void;
};

function makeDraft(label: string, heure_debut: string, heure_fin: string): TrancheDraft {
  return { nom: label, heure_debut, heure_fin };
}

export default function TrancheRow({
  id,
  label,
  heure_debut,
  heure_fin,
  disabled = false,
  locked = false,
  isEditing = false,
  onStartEdit,
  onCancelEdit,
  onDelete,
  onSave,
}: TrancheRowProps) {
  const baseDraft = useMemo(
    () => makeDraft(label, heure_debut, heure_fin),
    [label, heure_debut, heure_fin]
  );

  const [draft, setDraft] = useState<TrancheDraft>(baseDraft);

  // Keep draft in sync with props when data changes from outside (refresh, optimistic updates, etc.)
  useEffect(() => {
    setDraft(baseDraft);
  }, [baseDraft]);

  // When leaving edit mode, always reset draft to source-of-truth props
  useEffect(() => {
    if (!isEditing) setDraft(baseDraft);
  }, [isEditing, baseDraft]);

  const actionsDisabled = disabled || locked;

  const isDirty = useMemo(() => {
    return (
      draft.nom !== label ||
      draft.heure_debut !== heure_debut ||
      draft.heure_fin !== heure_fin
    );
  }, [draft, label, heure_debut, heure_fin]);

  const canSave = useMemo(() => {
    if (actionsDisabled) return false;
    if (!isDirty) return false;

    if (draft.nom.trim().length === 0) return false;
    if (!isValidTimeHHMM(draft.heure_debut)) return false;
    if (!isValidTimeHHMM(draft.heure_fin)) return false;

    return true;
  }, [actionsDisabled, isDirty, draft]);

  const updateName = useCallback(
    (value: string) => setDraft((p) => ({ ...p, nom: value })),
    []
  );
  const updateStart = useCallback(
    (value: string) => setDraft((p) => ({ ...p, heure_debut: value })),
    []
  );
  const updateEnd = useCallback(
    (value: string) => setDraft((p) => ({ ...p, heure_fin: value })),
    []
  );

  const handleCancel = useCallback(() => {
    setDraft(baseDraft);
    onCancelEdit();
  }, [baseDraft, onCancelEdit]);

  const handleSave = useCallback(async () => {
    await onSave(draft);
  }, [draft, onSave]);

  return (
    <div className="flex items-center justify-between gap-3 rounded-xl bg-zinc-50 px-3 py-2 ring-1 ring-zinc-100">
      <div className="min-w-0">
        <div className="truncate text-sm text-zinc-900">{label}</div>
        {!isEditing ? (
          <div className="mt-0.5 text-xs text-zinc-600">
            {formatRange(heure_debut, heure_fin)}
          </div>
        ) : null}
      </div>

      <div className="flex items-center gap-2">
        {isEditing ? (
          <>
            <input
              className="w-28 rounded-lg border border-zinc-200 bg-white px-2 py-1 text-xs"
              value={draft.nom}
              onChange={(e) => updateName(e.target.value)}
              disabled={actionsDisabled}
              placeholder="GTI M"
              autoComplete="off"
              aria-label="Tranche name"
            />

            <input
              type="time"
              step={60}
              className="w-24 rounded-lg border border-zinc-200 bg-white px-2 py-1 text-xs"
              value={draft.heure_debut}
              onChange={(e) => updateStart(e.target.value)}
              disabled={actionsDisabled}
              aria-label="Start time"
            />

            <input
              type="time"
              step={60}
              className="w-24 rounded-lg border border-zinc-200 bg-white px-2 py-1 text-xs"
              value={draft.heure_fin}
              onChange={(e) => updateEnd(e.target.value)}
              disabled={actionsDisabled}
              aria-label="End time"
            />

            <Button
              type="button"
              variant="successSoft"
              size="compact"
              onClick={handleSave}
              disabled={!canSave}
              title={!canSave ? "Aucun changement à enregistrer" : "Enregistrer"}
            >
              OK
            </Button>

            <SecondaryButton
              type="button"
              size="compact"
              onClick={handleCancel}
              disabled={actionsDisabled}
            >
              Annuler
            </SecondaryButton>
          </>
        ) : (
          <SecondaryButton
            type="button"
            size="compact"
            onClick={onStartEdit}
            disabled={actionsDisabled}
          >
            Modifier
          </SecondaryButton>
        )}

        <Button
          type="button"
          variant="dangerSoft"
          size="compact"
          onClick={onDelete}
          disabled={actionsDisabled}
        >
          Supprimer
        </Button>
      </div>
    </div>
  );
}
