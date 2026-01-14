"use client";

import { useEffect, useMemo, useRef, useState } from "react";

import { Button, SecondaryButton, FormError, RequiredFieldsNote, SelectField, TextField } from "@/components/ui";
import { useRegimeOptions } from "@/features/regimes/useRegimeOptions";
import type { AgentDetails } from "@/types";

export type AgentFormValues = {
  nom: string;
  prenom: string;
  code_personnel: string;
  regime_id: string;
};

export default function AgentForm({
  mode,
  initialAgent,
  onSubmit,
  onCancel,
  submitting,
}: {
  mode: "create" | "edit";
  initialAgent?: AgentDetails | null;
  onSubmit: (values: {
    nom: string;
    prenom: string;
    code_personnel: string;
    regime_id: number | null;
  }) => Promise<void>;
  onCancel: () => void;
  submitting: boolean;
}) {
  const initial: AgentFormValues = useMemo(
    () => ({
      nom: initialAgent?.nom ?? "",
      prenom: initialAgent?.prenom ?? "",
      code_personnel: initialAgent?.code_personnel ?? "",
      regime_id: initialAgent?.regime_id != null ? String(initialAgent.regime_id) : "",
    }),
    [initialAgent]
  );

  const { options: regimeOptions, loading: regimesLoading, error: regimesError } = useRegimeOptions();

  const [values, setValues] = useState<AgentFormValues>(initial);
  const [error, setError] = useState<string | null>(null);

  const nomRef = useRef<HTMLInputElement | null>(null);

  useEffect(() => {
    setValues({
      nom: initialAgent?.nom ?? "",
      prenom: initialAgent?.prenom ?? "",
      code_personnel: initialAgent?.code_personnel ?? "",
      regime_id: initialAgent?.regime_id != null ? String(initialAgent.regime_id) : "",
    });
    setError(null);
  }, [initialAgent, mode]);

  useEffect(() => {
    // Auto focus on nom input
    const t = setTimeout(() => nomRef.current?.focus(), 0);
    return () => clearTimeout(t);
  }, [mode, initialAgent?.id]);

  function set<K extends keyof AgentFormValues>(key: K, v: AgentFormValues[K]) {
    setValues((prev) => ({ ...prev, [key]: v }));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);

    const nom = values.nom.trim();
    const prenom = values.prenom.trim();
    const code_personnel = values.code_personnel.trim();

    if (!nom || !prenom) {
      setError("Nom et prénom sont obligatoires.");
      return;
    }
    if (nom.length > 100 || prenom.length > 100) {
      setError("Nom et prénom doivent faire au maximum 100 caractères.");
      return;
    }
    if (code_personnel.length > 8) {
      setError("Le code personnel doit faire au maximum 8 caractères.");
      return;
    }

    const regimeRaw = values.regime_id.trim();
    const regime_id =
      regimeRaw === "" ? null : Number(regimeRaw);

    if (regimeRaw !== "" && Number.isNaN(regime_id)) {
      setError("Le régime doit être un nombre.");
      return;
    }

    try {
      await onSubmit({ nom, prenom, code_personnel, regime_id });
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erreur inconnue");
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <FormError message={error} />

      <div className="grid gap-3 sm:grid-cols-2">
        <TextField
          ref={nomRef}
          label="Nom"
          mandatory
          value={values.nom}
          onChange={(e) => set("nom", e.target.value)}
          placeholder="Dupont"
          disabled={submitting}
        />

        <TextField
          label="Prénom"
          mandatory
          value={values.prenom}
          onChange={(e) => set("prenom", e.target.value)}
          placeholder="Jean"
          disabled={submitting}
        />
      </div>

      <TextField
        label="Code personnel"
        value={values.code_personnel}
        onChange={(e) => set("code_personnel", e.target.value)}
        placeholder="1234567A"
        disabled={submitting}
      />

      <SelectField
        label="Régime"
        value={values.regime_id}
        onChange={(e) => set("regime_id", e.target.value)}
        options={regimeOptions}
        placeholder={regimesLoading ? "Chargement..." : "Sélectionner..."}
        hint={regimesError ? "Impossible de charger les régimes." : "Optionnel"}
        disabled={submitting || regimesLoading}
      />

      <div className="pt-1">
        <RequiredFieldsNote />
      </div>

      <div className="flex justify-end gap-2 pt-1">
        <SecondaryButton onClick={onCancel} disabled={submitting}>
          Annuler
        </SecondaryButton>

        <Button type="submit" loading={submitting} variant="success">
          {mode === "create" ? "Créer" : "Enregistrer"}
        </Button>
      </div>
    </form>
  );
}
