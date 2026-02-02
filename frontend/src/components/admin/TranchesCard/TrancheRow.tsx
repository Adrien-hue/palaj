"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import { Button } from "@/components/ui/button";
import { ColorPicker } from "@/components/ui/color-picker";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

import type { TrancheDraft } from "./types";
import { formatRange, isValidTimeHHMM } from "./helpers";

const HEX_RE = /^#[0-9A-Fa-f]{6}$/;

export type TrancheRowProps = {
  id: number;
  label: string;
  heure_debut: string; // "HH:MM"
  heure_fin: string; // "HH:MM"

  color?: string | null;

  disabled?: boolean;
  locked?: boolean;
  isEditing?: boolean;

  onStartEdit: () => void;
  onCancelEdit: () => void;
  onDelete: () => void;
  onSave: (draft: TrancheDraft) => Promise<void> | void;
};

function makeDraft(
  label: string,
  heure_debut: string,
  heure_fin: string,
  color?: string | null,
): TrancheDraft {
  return { nom: label, heure_debut, heure_fin, color: color ?? null };
}

export default function TrancheRow({
  id,
  label,
  heure_debut,
  heure_fin,
  color = null,
  disabled = false,
  locked = false,
  isEditing = false,
  onStartEdit,
  onCancelEdit,
  onDelete,
  onSave,
}: TrancheRowProps) {
  const baseDraft = useMemo(
    () => makeDraft(label, heure_debut, heure_fin, color),
    [label, heure_debut, heure_fin, color],
  );

  const [draft, setDraft] = useState<TrancheDraft>(baseDraft);

  useEffect(() => {
    setDraft(baseDraft);
  }, [baseDraft]);

  useEffect(() => {
    if (!isEditing) setDraft(baseDraft);
  }, [isEditing, baseDraft]);

  const actionsDisabled = disabled || locked;

  const isDirty = useMemo(() => {
    return (
      draft.nom !== label ||
      draft.heure_debut !== heure_debut ||
      draft.heure_fin !== heure_fin ||
      (draft.color ?? null) !== (color ?? null)
    );
  }, [draft, label, heure_debut, heure_fin, color]);

  const isColorValid = useMemo(() => {
    const v = draft.color;
    if (v == null || v === "") return true; // null = no color
    return HEX_RE.test(v);
  }, [draft.color]);

  const canSave = useMemo(() => {
    if (actionsDisabled) return false;
    if (!isDirty) return false;

    if (draft.nom.trim().length === 0) return false;
    if (!isValidTimeHHMM(draft.heure_debut)) return false;
    if (!isValidTimeHHMM(draft.heure_fin)) return false;
    if (!isColorValid) return false;

    return true;
  }, [actionsDisabled, isDirty, draft, isColorValid]);

  const updateName = useCallback(
    (value: string) => setDraft((p) => ({ ...p, nom: value })),
    [],
  );
  const updateStart = useCallback(
    (value: string) => setDraft((p) => ({ ...p, heure_debut: value })),
    [],
  );
  const updateEnd = useCallback(
    (value: string) => setDraft((p) => ({ ...p, heure_fin: value })),
    [],
  );

  const updateColor = useCallback((value: string | null) => {
    setDraft((p) => ({ ...p, color: value }));
  }, []);

  const handleCancel = useCallback(() => {
    setDraft(baseDraft);
    onCancelEdit();
  }, [baseDraft, onCancelEdit]);

  const handleSave = useCallback(async () => {
    // Normalise : uppercase + null si vide
    const v = draft.color;
    const normalized =
      v == null || v.trim() === "" ? null : v.trim().toUpperCase();

    await onSave({ ...draft, color: normalized });
  }, [draft, onSave]);

  return (
    <div className="rounded-xl border bg-muted/30 p-3">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="truncate text-sm font-medium">{label}</div>
          {!isEditing ? (
            <div className="mt-0.5 text-xs text-muted-foreground">
              {formatRange(heure_debut, heure_fin)}
            </div>
          ) : null}
        </div>

        <div className="flex shrink-0 items-center gap-2">
          {isEditing ? (
            <>
              <Button
                type="button"
                size="sm"
                onClick={handleSave}
                disabled={!canSave}
                title={
                  !canSave
                    ? !isColorValid
                      ? "Couleur invalide (format #RRGGBB)"
                      : "Aucun changement à enregistrer"
                    : "Enregistrer"
                }
              >
                Enregistrer
              </Button>

              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={handleCancel}
                disabled={actionsDisabled}
              >
                Annuler
              </Button>
            </>
          ) : (
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={onStartEdit}
              disabled={actionsDisabled}
            >
              Modifier
            </Button>
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

      {isEditing ? (
        <div className="mt-3 grid gap-3 sm:grid-cols-4">
          <div className="grid gap-1.5">
            <Label htmlFor={`tranche-${id}-nom`}>Nom</Label>
            <Input
              id={`tranche-${id}-nom`}
              value={draft.nom}
              onChange={(e) => updateName(e.target.value)}
              disabled={actionsDisabled}
              placeholder="GTI M"
              autoComplete="off"
            />
          </div>

          <div className="grid gap-1.5">
            <Label htmlFor={`tranche-${id}-start`}>Début</Label>
            <Input
              id={`tranche-${id}-start`}
              type="time"
              step={60}
              value={draft.heure_debut}
              onChange={(e) => updateStart(e.target.value)}
              disabled={actionsDisabled}
            />
          </div>

          <div className="grid gap-1.5">
            <Label htmlFor={`tranche-${id}-end`}>Fin</Label>
            <Input
              id={`tranche-${id}-end`}
              type="time"
              step={60}
              value={draft.heure_fin}
              onChange={(e) => updateEnd(e.target.value)}
              disabled={actionsDisabled}
            />
          </div>

          <div className="grid gap-1.5">
            <ColorPicker
              id={`tranche-${id}-color`}
              label="Couleur"
              value={draft.color ?? null}
              disabled={actionsDisabled}
              onChange={(next) => updateColor(next)}
            />
          </div>
        </div>
      ) : null}
    </div>
  );
}
