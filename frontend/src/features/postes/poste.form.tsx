"use client";

import { useEffect, useRef, useState } from "react";
import { Button, FormError, RequiredFieldsNote, SecondaryButton, TextField } from "@/components/ui";
import type { Poste } from "@/types";

type Values = { nom: string };

export default function PosteForm({
  mode,
  initialPoste,
  onSubmit,
  onCancel,
  submitting,
}: {
  mode: "create" | "edit";
  initialPoste?: Poste | null;
  onSubmit: (values: { nom: string }) => Promise<void>;
  onCancel: () => void;
  submitting: boolean;
}) {
  const [values, setValues] = useState<Values>({ nom: "" });
  const [error, setError] = useState<string | null>(null);

  const nomRef = useRef<HTMLInputElement | null>(null);

  useEffect(() => {
    setValues({ nom: initialPoste?.nom ?? "" });
    setError(null);
  }, [initialPoste, mode]);

  useEffect(() => {
    // Auto focus on nom input
    const t = setTimeout(() => nomRef.current?.focus(), 0);
    return () => clearTimeout(t);
  }, [mode, initialPoste?.id]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);

    const nom = values.nom.trim();
    if (!nom) return setError("Le nom est obligatoire.");
    if (nom.length > 100) return setError("Le nom doit faire au maximum 100 caractères.");

    try {
      await onSubmit({ nom });
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erreur inconnue");
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <FormError message={error} />

      <TextField
        ref={nomRef}
        label="Nom"
        mandatory
        value={values.nom}
        onChange={(e) => setValues({ nom: e.target.value })}
        placeholder="ex: Conducteur, Agent de manœuvre..."
        disabled={submitting}
      />

      <div className="pt-1">
        <RequiredFieldsNote />
      </div>

      <div className="flex justify-end gap-2 pt-1">
        <SecondaryButton type="button" onClick={onCancel} disabled={submitting}>
          Annuler
        </SecondaryButton>
        <Button type="submit" variant="success" loading={submitting}>
          {mode === "create" ? "Créer" : "Enregistrer"}
        </Button>
      </div>
    </form>
  );
}
