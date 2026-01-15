"use client";

import { useCallback, useMemo } from "react";
import { Button, SecondaryButton } from "@/components/ui";
import type { TrancheDraft } from "./types";
import { isValidTimeHHMM } from "./helpers";

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

  return (
    <div className="mt-4 rounded-xl bg-zinc-50 p-3 ring-1 ring-zinc-200">
      <div className="text-sm font-semibold text-zinc-900">Add a tranche</div>
      <div className="mt-1 text-xs text-zinc-600">Name + start/end times.</div>

      <div className="mt-3 grid gap-2 sm:grid-cols-3">
        <label className="text-xs text-zinc-700">
          Name
          <input
            className="mt-1 w-full rounded-lg border border-zinc-200 bg-white px-2 py-2 text-sm"
            value={draft.nom}
            onChange={(e) => updateName(e.target.value)}
            disabled={disabled}
            placeholder="T1"
            autoComplete="off"
          />
        </label>

        <label className="text-xs text-zinc-700">
          Start
          <input
            type="time"
            className="mt-1 w-full rounded-lg border border-zinc-200 bg-white px-2 py-2 text-sm"
            value={draft.heure_debut}
            onChange={(e) => updateStart(e.target.value)}
            disabled={disabled}
            step={60} // minutes precision (keeps UI simple)
          />
        </label>

        <label className="text-xs text-zinc-700">
          End
          <input
            type="time"
            className="mt-1 w-full rounded-lg border border-zinc-200 bg-white px-2 py-2 text-sm"
            value={draft.heure_fin}
            onChange={(e) => updateEnd(e.target.value)}
            disabled={disabled}
            step={60}
          />
        </label>
      </div>

      <div className="mt-3 flex justify-end gap-2">
        <SecondaryButton type="button" size="compact" onClick={onCancel} disabled={disabled}>
          Cancel
        </SecondaryButton>

        <Button
          type="button"
          variant="successSoft"
          size="compact"
          onClick={onSubmit}
          disabled={!canSubmit}
          title={!canSubmit ? "Fill name + valid start/end times" : "Add tranche"}
        >
          Add
        </Button>
      </div>
    </div>
  );
}
