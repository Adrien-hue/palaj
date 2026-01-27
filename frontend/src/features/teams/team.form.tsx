"use client";

import * as React from "react";
import { useMemo, useState, useImperativeHandle } from "react";

import { buildTeamPatch } from "@/features/teams/buildTeamPatch";
import type { Team, TeamBase, PatchTeamBody } from "@/types";

// shadcn
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";

export type TeamFormHandle = {
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

export default React.forwardRef<
  TeamFormHandle,
  {
    mode: "create" | "edit";
    initialTeam?: Team | null;
    submitting?: boolean;
    onSubmit: (values: TeamBase) => void | Promise<void>;
  }
>(function TeamForm({ mode, initialTeam, submitting, onSubmit }, ref) {
  const isEdit = mode === "edit";
  const disabled = !!submitting;

  const [error, setError] = useState<string | null>(null);

  const [name, setName] = useState(initialTeam?.name ?? "");
  const [description, setDescription] = useState<string>(
    initialTeam?.description ?? ""
  );

  // Single source of truth for payload (normalized)
  const draft: TeamBase = useMemo(
    () => ({
      name: name.trim(),
      description: description.trim() ? description.trim() : null,
    }),
    [name, description]
  );

  const patch: PatchTeamBody = useMemo(() => {
    if (!isEdit || !initialTeam) return {};
    return buildTeamPatch(initialTeam, draft);
  }, [isEdit, initialTeam, draft]);

  const hasChanges = useMemo(() => {
    if (!isEdit) return true;
    return Object.keys(patch).length > 0;
  }, [isEdit, patch]);

  const canSubmit = useMemo(() => {
    const n = draft.name;
    const validName = n.length >= 2 && n.length <= 120;
    return validName && !disabled && hasChanges;
  }, [draft.name, disabled, hasChanges]);

  function buildValues(): TeamBase {
    return {
      name: name.trim(),
      description: description.trim() ? description.trim() : null,
    };
  }

  async function handleSubmit() {
    setError(null);

    if (!canSubmit) {
      const n = draft.name.trim();
      if (!n) setError("Le nom est obligatoire.");
      else if (n.length < 2) setError("Le nom doit contenir au moins 2 caractères.");
      else if (n.length > 120) setError("Le nom ne doit pas dépasser 120 caractères.");
      else if (isEdit && !hasChanges) setError("Aucune modification à enregistrer.");
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
        <Field label="Nom" hint="Entre 2 et 120 caractères.">
          <Input
            value={name}
            onChange={(e) => setName(e.currentTarget.value)}
            disabled={disabled}
            maxLength={120}
            placeholder="Ex: GM"
          />
        </Field>

        <div className="sm:col-span-2">
          <Field label="Description" hint="Optionnel">
            <Textarea
              value={description}
              onChange={(e) => setDescription(e.currentTarget.value)}
              disabled={disabled}
              maxLength={1000}
              rows={3}
              placeholder="Optionnel"
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
