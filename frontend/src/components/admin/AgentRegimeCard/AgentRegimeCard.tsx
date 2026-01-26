"use client";

import { useEffect, useMemo, useState } from "react";

import { cn } from "@/lib/utils";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

import { AdminDetailsRow } from "@/components/admin/AdminDetailsRow";

import type { AgentRegimeCardProps, RegimeOption } from "./types";
import { normalizeDesc } from "./helpers";

export function AgentRegimeCard({
  title = "Régime",
  regime,
  loadOptions,
  disabled = false,
  onChangeRegime,
  onClearRegime,
  confirmClear,
}: AgentRegimeCardProps) {
  const [editing, setEditing] = useState(false);
  const [busy, setBusy] = useState(false);

  const [options, setOptions] = useState<RegimeOption[]>([]);
  const [optLoading, setOptLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const initialId = regime?.id ?? null;

  // Valeur Radix: jamais ""
  const NONE = "__none__";

  const [draftId, setDraftId] = useState<string>(initialId != null ? String(initialId) : NONE);
  const [selectedHint, setSelectedHint] = useState<string | null>(normalizeDesc(regime?.desc));

  // When parent regime changes (after save), sync draft if not editing
  useEffect(() => {
    if (editing) return;
    setDraftId(initialId != null ? String(initialId) : NONE);
    setSelectedHint(normalizeDesc(regime?.desc));
  }, [editing, initialId, regime?.desc]);

  // Load options once
  useEffect(() => {
    let cancelled = false;

    async function run() {
      setOptLoading(true);
      setError(null);
      try {
        const opts = await loadOptions();
        if (!cancelled) setOptions(opts);
      } catch (e: any) {
        if (!cancelled) setError(e?.message ?? "Impossible de charger les régimes.");
      } finally {
        if (!cancelled) setOptLoading(false);
      }
    }

    run();
    return () => {
      cancelled = true;
    };
  }, [loadOptions]);

  const optionById = useMemo(() => {
    const m = new Map<number, RegimeOption>();
    for (const o of options) m.set(o.id, o);
    return m;
  }, [options]);

  const canEdit = !disabled && !busy;
  const locked = disabled || busy;

  const isDirty = useMemo(() => {
    const cur = initialId != null ? String(initialId) : NONE;
    return draftId !== cur;
  }, [draftId, initialId]);

  const canSave = editing && canEdit && draftId !== NONE && isDirty;

  async function handleSave() {
    if (!canSave) return;
    setError(null);
    setBusy(true);
    try {
      await onChangeRegime(Number(draftId));
      setEditing(false);
    } catch (e: any) {
      setError(e?.message ?? "Enregistrement impossible.");
    } finally {
      setBusy(false);
    }
  }

  function handleCancel() {
    if (locked) return;
    setDraftId(initialId != null ? String(initialId) : NONE);
    setSelectedHint(normalizeDesc(regime?.desc));
    setEditing(false);
    setError(null);
  }

  async function handleClear() {
    if (locked) return;
    if (!regime) return;

    const ok = await confirmClear(regime.nom);
    if (!ok) return;

    setError(null);
    setBusy(true);
    try {
      await onClearRegime();
      setEditing(false);
      setDraftId(NONE);
      setSelectedHint(null);
    } catch (e: any) {
      setError(e?.message ?? "Suppression impossible.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-base">{title}</CardTitle>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Summary */}
        {regime ? (
          <div className="grid gap-0">
            <AdminDetailsRow label="Nom" value={regime.nom} />
            <AdminDetailsRow label="Description" value={regime.desc || "—"} />
          </div>
        ) : (
          <div className="text-sm text-muted-foreground">Aucun régime.</div>
        )}

        {error ? (
          <Alert variant="destructive">
            <AlertTitle>Erreur</AlertTitle>
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        ) : null}

        {!editing ? (
          <div className="flex justify-end">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => {
                if (!canEdit) return;
                setEditing(true);

                // Preselect first option if none
                if (draftId === NONE && options.length > 0) {
                  const first = options[0];
                  setDraftId(String(first.id));
                  setSelectedHint(first.hint ?? null);
                }
              }}
              disabled={!canEdit || optLoading}
            >
              Modifier
            </Button>
          </div>
        ) : (
          <div className={cn("rounded-xl border bg-muted/30 p-4", locked && "opacity-80")}>
            <div className="text-xs font-medium text-foreground">
              Choisir un régime
            </div>

            <div className="mt-2 space-y-2">
              <Select
                value={draftId}
                onValueChange={(v) => {
                  setDraftId(v);

                  if (v !== NONE) {
                    const opt = optionById.get(Number(v));
                    setSelectedHint(opt?.hint ?? null);
                  } else {
                    setSelectedHint(null);
                  }
                }}
                disabled={locked || optLoading}
              >
                <SelectTrigger>
                  <SelectValue placeholder={optLoading ? "Chargement…" : "Sélectionner…"} />
                </SelectTrigger>

                <SelectContent>
                  {/* Option "aucun" (radix interdit "") */}
                  <SelectItem value={NONE}>Aucun régime</SelectItem>

                  {options.map((o) => (
                    <SelectItem key={o.id} value={String(o.id)}>
                      {o.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>

              <div className="text-xs text-muted-foreground">
                {selectedHint ? selectedHint : "—"}
              </div>
            </div>

            <div className="mt-4 flex items-center justify-between gap-2">
              <Button
                type="button"
                variant="destructive"
                size="sm"
                onClick={handleClear}
                disabled={locked || !regime}
                title={!regime ? "Aucun régime à retirer" : "Retirer le régime"}
              >
                Retirer
              </Button>

              <div className="flex items-center gap-2">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={handleCancel}
                  disabled={locked}
                >
                  Annuler
                </Button>

                <Button
                  type="button"
                  size="sm"
                  onClick={handleSave}
                  disabled={!canSave}
                >
                  {busy ? "Enregistrement…" : "Enregistrer"}
                </Button>
              </div>
            </div>
          </div>
        )}

        {optLoading ? (
          <div className="text-xs text-muted-foreground">Chargement…</div>
        ) : null}
      </CardContent>
    </Card>
  );
}
