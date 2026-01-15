// frontend/src/components/admin/QualificationCard/AddQualificationPanel.tsx
"use client";

import { Button, SecondaryButton } from "@/components/ui";
import type { QualificationOption } from "./types";

export default function AddQualificationPanel({
  entityLabel,
  disabled,
  optLoading,
  availableOptions,
  addRelatedId,
  addDate,
  onChangeRelatedId,
  onChangeDate,
  onCancel,
  onSubmit,
}: {
  entityLabel: string;
  disabled: boolean;
  optLoading: boolean;
  availableOptions: QualificationOption[];
  addRelatedId: number | "";
  addDate: string;
  onChangeRelatedId: (v: number | "") => void;
  onChangeDate: (v: string) => void;
  onCancel: () => void;
  onSubmit: () => void;
}) {
  const canSubmit = !disabled && addRelatedId !== "" && !!addDate && availableOptions.length > 0;

  return (
    <div className="mt-4 rounded-xl bg-zinc-50 p-3 ring-1 ring-zinc-200">
      <div className="text-sm font-semibold text-zinc-900">Ajouter une qualification</div>

      <div className="mt-1 text-xs text-zinc-600">
        {availableOptions.length === 0
          ? `Aucun ${entityLabel.toLowerCase()} disponible à ajouter.`
          : `${availableOptions.length} disponible(s)`}
      </div>

      <div className="mt-3 grid gap-2 sm:grid-cols-2">
        <label className="text-xs text-zinc-700">
          {entityLabel}
          <select
            className="mt-1 w-full rounded-lg border border-zinc-200 bg-white px-2 py-2 text-sm"
            value={addRelatedId}
            onChange={(e) => onChangeRelatedId(e.target.value ? Number(e.target.value) : "")}
            disabled={disabled || optLoading || availableOptions.length === 0}
          >
            <option value="">— Choose —</option>
            {availableOptions.map((o) => (
              <option key={o.id} value={o.id}>
                {o.label}
              </option>
            ))}
          </select>
        </label>

        <label className="text-xs text-zinc-700">
          Date de qualification
          <input
            type="date"
            className="mt-1 w-full rounded-lg border border-zinc-200 bg-white px-2 py-2 text-sm"
            value={addDate}
            onChange={(e) => onChangeDate(e.target.value)}
            disabled={disabled}
          />
        </label>
      </div>

      <div className="mt-3 flex justify-end gap-2">
        <SecondaryButton type="button" size="compact" onClick={onCancel} disabled={disabled}>
          Annuler
        </SecondaryButton>

        <Button type="button" variant="successSoft" size="compact" onClick={onSubmit} disabled={!canSubmit}>
          Ajouter
        </Button>
      </div>

      {optLoading ? <div className="mt-2 text-xs text-zinc-600">Chargement...</div> : null}
    </div>
  );
}
