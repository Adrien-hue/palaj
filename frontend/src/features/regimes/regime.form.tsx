"use client";

import { useMemo, useState } from "react";
import {
  Button,
  SecondaryButton,
  LongTextField,
  NumberField,
  RequiredFieldsNote,
  TextField,
} from "@/components/ui";
import { buildRegimePatch } from "@/features/regimes/buildRegimePatch";
import type {
  CreateRegimeBody,
  Regime,
  RegimeBase,
  UpdateRegimeBody,
} from "@/types";
import { parseNullableInt, toInputValue } from "@/lib/forms/inputs";

export default function RegimeForm({
  mode,
  initialRegime,
  submitting,
  onCancel,
  onSubmit,
}: {
  mode: "create" | "edit";
  initialRegime?: Regime | null;
  submitting?: boolean;
  onCancel: () => void;
  onSubmit: (values: RegimeBase) => void | Promise<void>;
}) {
  const isEdit = mode === "edit";

  const [nom, setNom] = useState(initialRegime?.nom ?? "");
  const [desc, setDesc] = useState(initialRegime?.desc ?? "");

  // numeric fields as strings (easy UX)
  const [minRpAnnuels, setMinRpAnnuels] = useState(
    toInputValue(initialRegime?.min_rp_annuels)
  );
  const [minRpDimanches, setMinRpDimanches] = useState(
    toInputValue(initialRegime?.min_rp_dimanches)
  );
  const [minRpsd, setMinRpsd] = useState(toInputValue(initialRegime?.min_rpsd));
  const [minRp2plus, setMinRp2plus] = useState(
    toInputValue(initialRegime?.min_rp_2plus)
  );
  const [minRpSemestre, setMinRpSemestre] = useState(
    toInputValue(initialRegime?.min_rp_semestre)
  );
  const [avgServiceMinutes, setAvgServiceMinutes] = useState(
    toInputValue(initialRegime?.avg_service_minutes)
  );
  const [avgToleranceMinutes, setAvgToleranceMinutes] = useState(
    toInputValue(initialRegime?.avg_tolerance_minutes)
  );

  // Single source of truth for payload
  const draft: CreateRegimeBody = useMemo(
    () => ({
      nom: nom.trim(),
      desc: desc.trim() ? desc.trim() : null,

      min_rp_annuels: parseNullableInt(minRpAnnuels),
      min_rp_dimanches: parseNullableInt(minRpDimanches),
      min_rpsd: parseNullableInt(minRpsd),
      min_rp_2plus: parseNullableInt(minRp2plus),
      min_rp_semestre: parseNullableInt(minRpSemestre),

      avg_service_minutes: parseNullableInt(avgServiceMinutes),
      avg_tolerance_minutes: parseNullableInt(avgToleranceMinutes),
    }),
    [
      nom,
      desc,
      minRpAnnuels,
      minRpDimanches,
      minRpsd,
      minRp2plus,
      minRpSemestre,
      avgServiceMinutes,
      avgToleranceMinutes,
    ]
  );

  const patch: UpdateRegimeBody = useMemo(() => {
    if (!isEdit || !initialRegime) return {};
    return buildRegimePatch(initialRegime, draft);
  }, [isEdit, initialRegime, draft]);

  const hasChanges = useMemo(() => {
    if (!isEdit) return true;
    return Object.keys(patch).length > 0;
  }, [isEdit, patch]);

  const canSubmit = useMemo(() => {
    const n = draft.nom;
    const validNom = n.length >= 1 && n.length <= 100;
    return validNom && !submitting && hasChanges;
  }, [draft.nom, submitting, hasChanges]);

  function buildValues(): RegimeBase {
    return {
      nom: nom.trim(),
      desc: desc.trim() ? desc.trim() : null,

      min_rp_annuels: parseNullableInt(minRpAnnuels),
      min_rp_dimanches: parseNullableInt(minRpDimanches),
      min_rpsd: parseNullableInt(minRpsd),
      min_rp_2plus: parseNullableInt(minRp2plus),
      min_rp_semestre: parseNullableInt(minRpSemestre),

      avg_service_minutes: parseNullableInt(avgServiceMinutes),
      avg_tolerance_minutes: parseNullableInt(avgToleranceMinutes),
    };
  }

  async function handleSubmit() {
    if (!canSubmit) return;
    await onSubmit(buildValues());
  }

  const submitLabel = isEdit ? "Enregistrer" : "Créer";
  const submitTitle = isEdit && !hasChanges ? "Aucune modification" : undefined;

  return (
    <div className="space-y-4">
      <div className="grid gap-3 sm:grid-cols-2">
        <TextField
          label="Nom"
          value={nom}
          onChange={(e) => setNom(e.currentTarget.value)}
          disabled={!!submitting}
          maxLength={100}
          placeholder="Ex: Régime A"
          mandatory
        />

        <div className="sm:col-span-2">
          <LongTextField
            label="Description"
            value={desc ?? ""}
            onChange={setDesc}
            disabled={!!submitting}
            maxLength={1000}
            rows={3}
            placeholder="Optionnel"
          />
        </div>
      </div>

      <div className="rounded-2xl bg-zinc-50 p-3 ring-1 ring-zinc-200">
        <div className="text-sm font-semibold text-zinc-900">Règles</div>
        <div className="mt-3 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          <NumberField
            label="Min RP annuels"
            value={minRpAnnuels}
            onChange={setMinRpAnnuels}
            disabled={!!submitting}
            allowNegative={false}
            allowFloat={false}
          />
          <NumberField
            label="Min RP dimanches"
            value={minRpDimanches}
            onChange={setMinRpDimanches}
            disabled={!!submitting}
            allowNegative={false}
            allowFloat={false}
          />
          <NumberField
            label="Min RPSD"
            value={minRpsd}
            onChange={setMinRpsd}
            disabled={!!submitting}
            allowNegative={false}
            allowFloat={false}
          />
          <NumberField
            label="Min RP 2+"
            value={minRp2plus}
            onChange={setMinRp2plus}
            disabled={!!submitting}
            allowNegative={false}
            allowFloat={false}
          />
          <NumberField
            label="Min RP semestre"
            value={minRpSemestre}
            onChange={setMinRpSemestre}
            disabled={!!submitting}
            allowNegative={false}
            allowFloat={false}
          />
        </div>
      </div>

      <div className="rounded-2xl bg-zinc-50 p-3 ring-1 ring-zinc-200">
        <div className="text-sm font-semibold text-zinc-900">Moyennes</div>
        <div className="mt-3 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          <NumberField
            label="Avg service (min)"
            value={avgServiceMinutes}
            onChange={setAvgServiceMinutes}
            disabled={!!submitting}
            allowNegative={false}
            allowFloat={false}
          />
          <NumberField
            label="Avg tolerance (min)"
            value={avgToleranceMinutes}
            onChange={setAvgToleranceMinutes}
            disabled={!!submitting}
            allowNegative={false}
            allowFloat={false}
          />
        </div>
      </div>

      <div className="pt-1">
        <RequiredFieldsNote />
      </div>

      <div className="flex justify-end gap-2">
        <SecondaryButton
          type="button"
          onClick={onCancel}
          disabled={!!submitting}
        >
          Annuler
        </SecondaryButton>

        <Button
          type="button"
          variant="success"
          onClick={handleSubmit}
          loading={!!submitting}
          disabled={!canSubmit}
        >
          {isEdit ? "Enregistrer" : "Créer"}
        </Button>
      </div>
    </div>
  );
}
