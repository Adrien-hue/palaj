"use client";

import * as React from "react";
import { useMemo, useState, useImperativeHandle } from "react";

import { buildRegimePatch } from "@/features/regimes/buildRegimePatch";
import type { CreateRegimeBody, Regime, RegimeBase, UpdateRegimeBody } from "@/types";
import { parseNullableInt, toInputValue } from "@/lib/forms/inputs";

// shadcn
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";

export type RegimeFormHandle = {
  submit: () => void;
};

function Field({
  label,
  children,
  hint,
}: {
  label: string;
  children: React.ReactNode;
  hint?: string;
}) {
  return (
    <div className="space-y-1.5">
      <Label className="text-sm">{label}</Label>
      {children}
      {hint ? <p className="text-xs text-muted-foreground">{hint}</p> : null}
    </div>
  );
}

export default React.forwardRef<RegimeFormHandle, {
  mode: "create" | "edit";
  initialRegime?: Regime | null;
  submitting?: boolean;
  onSubmit: (values: RegimeBase) => void | Promise<void>;
}>(function RegimeForm(
  { mode, initialRegime, submitting, onSubmit },
  ref
) {
  const isEdit = mode === "edit";
  const disabled = !!submitting;

  const [error, setError] = useState<string | null>(null);

  const [nom, setNom] = useState(initialRegime?.nom ?? "");
  const [desc, setDesc] = useState(initialRegime?.desc ?? "");

  // numeric fields as strings (easy UX)
  const [minRpAnnuels, setMinRpAnnuels] = useState(toInputValue(initialRegime?.min_rp_annuels));
  const [minRpDimanches, setMinRpDimanches] = useState(toInputValue(initialRegime?.min_rp_dimanches));
  const [minRpsd, setMinRpsd] = useState(toInputValue(initialRegime?.min_rpsd));
  const [minRp2plus, setMinRp2plus] = useState(toInputValue(initialRegime?.min_rp_2plus));
  const [minRpSemestre, setMinRpSemestre] = useState(toInputValue(initialRegime?.min_rp_semestre));
  const [avgServiceMinutes, setAvgServiceMinutes] = useState(toInputValue(initialRegime?.avg_service_minutes));
  const [avgToleranceMinutes, setAvgToleranceMinutes] = useState(toInputValue(initialRegime?.avg_tolerance_minutes));

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
    return validNom && !disabled && hasChanges;
  }, [draft.nom, disabled, hasChanges]);

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
    setError(null);

    if (!canSubmit) {
      if (!draft.nom.trim()) setError("Le nom est obligatoire.");
      return;
    }

    try {
      await onSubmit(buildValues());
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erreur inconnue");
    }
  }

  useImperativeHandle(ref, () => ({
    submit: () => {
      void handleSubmit();
    },
  }));

  return (
    <div className="space-y-6">
      {error ? (
        <Alert variant="destructive">
          <AlertTitle>Erreur</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      ) : null}

      <div className="grid gap-4 sm:grid-cols-2">
        <Field label="Nom">
          <Input
            value={nom}
            onChange={(e) => setNom(e.currentTarget.value)}
            disabled={disabled}
            maxLength={100}
            placeholder="Ex: Régime A"
          />
        </Field>

        <div className="sm:col-span-2">
          <Field label="Description" hint="Optionnel">
            <Textarea
              value={desc ?? ""}
              onChange={(e) => setDesc(e.currentTarget.value)}
              disabled={disabled}
              maxLength={1000}
              rows={3}
              placeholder="Optionnel"
            />
          </Field>
        </div>
      </div>

      <div className="rounded-xl border bg-muted/30 p-4">
        <div className="text-sm font-semibold">Règles</div>
        <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <Field label="Min RP annuels">
            <Input
              inputMode="numeric"
              value={minRpAnnuels}
              onChange={(e) => setMinRpAnnuels(e.currentTarget.value)}
              disabled={disabled}
              placeholder="0"
            />
          </Field>

          <Field label="Min RP dimanches">
            <Input
              inputMode="numeric"
              value={minRpDimanches}
              onChange={(e) => setMinRpDimanches(e.currentTarget.value)}
              disabled={disabled}
              placeholder="0"
            />
          </Field>

          <Field label="Min RPSD">
            <Input
              inputMode="numeric"
              value={minRpsd}
              onChange={(e) => setMinRpsd(e.currentTarget.value)}
              disabled={disabled}
              placeholder="0"
            />
          </Field>

          <Field label="Min RP 2+">
            <Input
              inputMode="numeric"
              value={minRp2plus}
              onChange={(e) => setMinRp2plus(e.currentTarget.value)}
              disabled={disabled}
              placeholder="0"
            />
          </Field>

          <Field label="Min RP semestre">
            <Input
              inputMode="numeric"
              value={minRpSemestre}
              onChange={(e) => setMinRpSemestre(e.currentTarget.value)}
              disabled={disabled}
              placeholder="0"
            />
          </Field>
        </div>
      </div>

      <div className="rounded-xl border bg-muted/30 p-4">
        <div className="text-sm font-semibold">Moyennes</div>
        <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <Field label="Avg service (min)">
            <Input
              inputMode="numeric"
              value={avgServiceMinutes}
              onChange={(e) => setAvgServiceMinutes(e.currentTarget.value)}
              disabled={disabled}
              placeholder="0"
            />
          </Field>

          <Field label="Avg tolerance (min)">
            <Input
              inputMode="numeric"
              value={avgToleranceMinutes}
              onChange={(e) => setAvgToleranceMinutes(e.currentTarget.value)}
              disabled={disabled}
              placeholder="0"
            />
          </Field>
        </div>
      </div>

      {isEdit && !hasChanges ? (
        <p className="text-xs text-muted-foreground">
          Aucune modification à enregistrer.
        </p>
      ) : null}
    </div>
  );
});
