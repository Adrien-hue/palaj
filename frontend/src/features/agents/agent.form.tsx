"use client";

import * as React from "react";
import { useEffect, useMemo, useRef, useState } from "react";
import { useForm } from "react-hook-form";

import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";

import type { AgentDetails } from "@/types";
import { useRegimeOptions, NO_REGIME_VALUE } from "@/features/regimes/useRegimeOptions";

import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

const MAX_NAME_LEN = 100;
const MAX_CODE_LEN = 8;

const schema = z.object({
  nom: z
    .string()
    .trim()
    .min(1, "Nom et prénom sont obligatoires.")
    .max(MAX_NAME_LEN, `Nom et prénom doivent faire au maximum ${MAX_NAME_LEN} caractères.`),

  prenom: z
    .string()
    .trim()
    .min(1, "Nom et prénom sont obligatoires.")
    .max(MAX_NAME_LEN, `Nom et prénom doivent faire au maximum ${MAX_NAME_LEN} caractères.`),

  code_personnel: z
    .string()
    .trim()
    .max(MAX_CODE_LEN, `Le code personnel doit faire au maximum ${MAX_CODE_LEN} caractères.`)
    .optional()
    .or(z.literal("")),

  regime_id: z.string().optional().or(z.literal(NO_REGIME_VALUE)),
});

export type AgentFormValues = z.infer<typeof schema>;

export type AgentFormHandle = {
  submit: () => void;
};

type Props = {
  mode: "create" | "edit";
  initialAgent?: AgentDetails | null;
  submitting: boolean;
  onSubmit: (values: {
    nom: string;
    prenom: string;
    code_personnel: string;
    regime_id: number | null;
  }) => Promise<void>;
};

const AgentForm = React.forwardRef<AgentFormHandle, Props>(function AgentForm(
  { mode, initialAgent, submitting, onSubmit },
  ref
) {
  const { options: regimeOptions, loading: regimesLoading, error: regimesError } =
    useRegimeOptions({ includeNone: true });

  const defaultValues: AgentFormValues = useMemo(
    () => ({
      nom: initialAgent?.nom ?? "",
      prenom: initialAgent?.prenom ?? "",
      code_personnel: initialAgent?.code_personnel ?? "",
      regime_id:
        initialAgent?.regime_id != null ? String(initialAgent.regime_id) : NO_REGIME_VALUE,
    }),
    [initialAgent]
  );

  const form = useForm<AgentFormValues>({
    resolver: zodResolver(schema),
    defaultValues,
    mode: "onSubmit",
  });

  // Reset quand on change d'agent / de mode (re-open dialog)
  useEffect(() => {
    form.reset(defaultValues);
    setServerError(null);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [defaultValues, mode]);

  // Autofocus "Nom"
  const nomRef = useRef<HTMLInputElement | null>(null);
  useEffect(() => {
    const t = setTimeout(() => nomRef.current?.focus(), 0);
    return () => clearTimeout(t);
  }, [mode, initialAgent?.id]);

  const [serverError, setServerError] = useState<string | null>(null);

  const submitInternal = form.handleSubmit(async (values) => {
    setServerError(null);

    const nom = values.nom.trim();
    const prenom = values.prenom.trim();
    const code_personnel = (values.code_personnel ?? "").trim();

    const regimeRaw = values.regime_id ?? NO_REGIME_VALUE;
    const regime_id = regimeRaw === NO_REGIME_VALUE ? null : Number(regimeRaw);

    if (regimeRaw !== NO_REGIME_VALUE && Number.isNaN(regime_id)) {
      setServerError("Le régime doit être un nombre.");
      return;
    }

    try {
      await onSubmit({ nom, prenom, code_personnel, regime_id });
    } catch (e) {
      setServerError(e instanceof Error ? e.message : "Erreur inconnue");
    }
  });

  // Expose submit() au parent (Dialog footer)
  React.useImperativeHandle(
    ref,
    () => ({
      submit: () => submitInternal(),
    }),
    [submitInternal]
  );

  return (
    <Form {...form}>
      {/* on garde un <form> pour l’accessibilité, mais on submit depuis le footer */}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          submitInternal();
        }}
        className="space-y-5"
      >
        {serverError ? (
          <Alert variant="destructive">
            <AlertTitle>Erreur</AlertTitle>
            <AlertDescription>{serverError}</AlertDescription>
          </Alert>
        ) : null}

        <div className="grid gap-4 sm:grid-cols-2">
          <FormField
            control={form.control}
            name="nom"
            render={({ field }) => (
              <FormItem>
                <FormLabel>
                  Nom <span className="text-destructive">*</span>
                </FormLabel>
                <FormControl>
                  <Input
                    {...field}
                    ref={(el) => {
                      field.ref(el);
                      nomRef.current = el;
                    }}
                    placeholder="Dupont"
                    disabled={submitting}
                    autoComplete="family-name"
                  />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="prenom"
            render={({ field }) => (
              <FormItem>
                <FormLabel>
                  Prénom <span className="text-destructive">*</span>
                </FormLabel>
                <FormControl>
                  <Input
                    {...field}
                    placeholder="Jean"
                    disabled={submitting}
                    autoComplete="given-name"
                  />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
        </div>

        <FormField
          control={form.control}
          name="code_personnel"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Code personnel</FormLabel>
              <FormControl>
                <Input
                  {...field}
                  placeholder="1234567A"
                  disabled={submitting}
                />
              </FormControl>
              <FormDescription>
                Optionnel — {MAX_CODE_LEN} caractères max.
              </FormDescription>
              <FormMessage />
            </FormItem>
          )}
        />

        <FormField
          control={form.control}
          name="regime_id"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Régime</FormLabel>
              <Select
                value={field.value ?? NO_REGIME_VALUE}
                onValueChange={(v) => field.onChange(v)}
                disabled={submitting || regimesLoading}
              >
                <FormControl>
                  <SelectTrigger>
                    <SelectValue
                      placeholder={regimesLoading ? "Chargement…" : "Sélectionner…"}
                    />
                  </SelectTrigger>
                </FormControl>

                <SelectContent>
                  {regimeOptions
                    .filter((o) => String(o.value).trim() !== "")
                    .map((opt) => (
                      <SelectItem key={String(opt.value)} value={String(opt.value)}>
                        {opt.label}
                      </SelectItem>
                    ))}
                </SelectContent>
              </Select>

              <FormDescription>
                {regimesError ? "Impossible de charger les régimes." : "Optionnel"}
              </FormDescription>
              <FormMessage />
            </FormItem>
          )}
        />

        <p className="text-xs text-muted-foreground">
          <span className="text-destructive">*</span> Champs obligatoires
        </p>
      </form>
    </Form>
  );
});

export default AgentForm;
