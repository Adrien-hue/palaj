"use client";

import * as React from "react";
import { useEffect, useImperativeHandle, useMemo, useRef, useState } from "react";

import type { Poste } from "@/types";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export type PosteFormHandle = {
  submit: () => void;
};

type PosteFormValues = {
  nom: string;
};

type PosteFormProps = {
  mode: "create" | "edit";
  initialPoste?: Poste | null;
  submitting: boolean;
  onSubmit: (values: { nom: string }) => Promise<void>;
};

const PosteFormInner = React.forwardRef<PosteFormHandle, PosteFormProps>(
  function PosteFormInner({ mode, initialPoste, submitting, onSubmit }, ref) {
    const initial: PosteFormValues = useMemo(
      () => ({ nom: initialPoste?.nom ?? "" }),
      [initialPoste]
    );

    const [values, setValues] = useState<PosteFormValues>(initial);
    const [error, setError] = useState<string | null>(null);

    const nomRef = useRef<HTMLInputElement | null>(null);
    const formRef = useRef<HTMLFormElement | null>(null);

    useEffect(() => {
      const t = setTimeout(() => nomRef.current?.focus(), 0);
      return () => clearTimeout(t);
    }, [mode, initialPoste?.id]);

    function validate(v: PosteFormValues) {
      const nom = v.nom.trim();
      if (!nom) return "Le nom est obligatoire.";
      if (nom.length > 100) return "Le nom doit faire au maximum 100 caractères.";
      return null;
    }

    async function handleSubmit() {
      if (submitting) return;

      setError(null);

      const err = validate(values);
      if (err) {
        setError(err);
        return;
      }

      try {
        await onSubmit({ nom: values.nom.trim() });
      } catch (e) {
        setError(e instanceof Error ? e.message : "Erreur inconnue");
      }
    }

    useImperativeHandle(
      ref,
      () => ({
        submit: () => formRef.current?.requestSubmit(),
      }),
      []
    );

    return (
      <form
        ref={formRef}
        onSubmit={(e) => {
          e.preventDefault();
          handleSubmit();
        }}
        className="space-y-4"
      >
        {error ? (
          <Alert variant="destructive">
            <AlertTitle>Erreur</AlertTitle>
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        ) : null}

        <div className="space-y-2">
          <Label htmlFor="poste-nom">
            Nom <span className="text-destructive">*</span>
          </Label>
          <Input
            id="poste-nom"
            ref={nomRef}
            value={values.nom}
            onChange={(e) => setValues({ nom: e.target.value })}
            placeholder="Ex : Conducteur, Agent de manœuvre…"
            disabled={submitting}
            maxLength={100}
          />
          <p className="text-xs text-muted-foreground">Max 100 caractères.</p>
        </div>

        <p className="text-xs text-muted-foreground">
          <span className="text-destructive">*</span> Champ obligatoire
        </p>
      </form>
    );
  }
);

export default React.forwardRef<PosteFormHandle, PosteFormProps>(
  function PosteForm(props, ref) {
    const { mode, initialPoste } = props;
    const formKey = `${mode}:${initialPoste?.id ?? "new"}`;

    return <PosteFormInner key={formKey} ref={ref} {...props} />;
  }
);
