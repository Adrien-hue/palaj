"use client";

import { useCallback, useMemo } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ColorPicker } from "@/components/ui/color-picker";

import type { TrancheDraft } from "./types";
import { isValidTimeHHMM } from "./helpers";

const HEX_RE = /^#[0-9A-Fa-f]{6}$/;
function isValidHex(v: string | null | undefined): boolean {
  if (v == null || v === "") return true;
  return HEX_RE.test(v);
}

export type AddTranchePanelProps = {
  disabled: boolean;
  draft: TrancheDraft;
  onChange: (next: TrancheDraft) => void;
  onCancel: () => void;
  onSubmit: () => void;
};

export default function AddTranchePanel({
  disabled,
  draft,
  onChange,
  onCancel,
  onSubmit,
}: AddTranchePanelProps) {
  const canSubmit = useMemo(() => {
    if (disabled) return false;
    if (draft.nom.trim().length === 0) return false;
    if (!isValidTimeHHMM(draft.heure_debut)) return false;
    if (!isValidTimeHHMM(draft.heure_fin)) return false;
    if (!isValidHex(draft.color)) return false;
    return true;
  }, [disabled, draft]);

  const updateName = useCallback(
    (value: string) => onChange({ ...draft, nom: value }),
    [draft, onChange]
  );

  const updateStart = useCallback(
    (value: string) => onChange({ ...draft, heure_debut: value }),
    [draft, onChange]
  );

  const updateEnd = useCallback(
    (value: string) => onChange({ ...draft, heure_fin: value }),
    [draft, onChange]
  );

  const updateColor = useCallback(
    (value: string | null) => onChange({ ...draft, color: value }),
    [draft, onChange]
  );

  return (
    <div className="rounded-xl border bg-muted/30 p-3">
      <div className="text-sm font-semibold">Ajouter une tranche</div>
      <div className="mt-1 text-xs text-muted-foreground">
        Nom + horaires de début/fin (+ couleur optionnelle).
      </div>

      <div className="mt-3 grid gap-3 sm:grid-cols-4">
        <div className="grid gap-1.5">
          <Label htmlFor="tranche-nom">Nom</Label>
          <Input
            id="tranche-nom"
            value={draft.nom}
            onChange={(e) => updateName(e.target.value)}
            disabled={disabled}
            placeholder="T1"
            autoComplete="off"
          />
        </div>

        <div className="grid gap-1.5">
          <Label htmlFor="tranche-start">Début</Label>
          <Input
            id="tranche-start"
            type="time"
            value={draft.heure_debut}
            onChange={(e) => updateStart(e.target.value)}
            disabled={disabled}
            step={60}
          />
        </div>

        <div className="grid gap-1.5">
          <Label htmlFor="tranche-end">Fin</Label>
          <Input
            id="tranche-end"
            type="time"
            value={draft.heure_fin}
            onChange={(e) => updateEnd(e.target.value)}
            disabled={disabled}
            step={60}
          />
        </div>

        <ColorPicker
          id="tranche-color"
          label="Couleur"
          value={draft.color ?? null}
          disabled={disabled}
          onChange={updateColor}
        />
      </div>

      <div className="mt-3 flex justify-end gap-2">
        <Button
          type="button"
          variant="outline"
          onClick={onCancel}
          disabled={disabled}
        >
          Annuler
        </Button>

        <Button
          type="button"
          onClick={onSubmit}
          disabled={!canSubmit}
          title={
            !canSubmit
              ? "Nom + horaires valides requis (et couleur valide si renseignée)"
              : "Ajouter la tranche"
          }
        >
          Ajouter
        </Button>
      </div>
    </div>
  );
}