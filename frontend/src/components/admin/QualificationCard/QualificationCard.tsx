"use client";

import { useEffect, useMemo, useState } from "react";

import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";

import AddQualificationPanel from "./AddQualificationPanel";
import QualificationRow from "./QualificationRow";
import QualificationCardHeader from "./QualificationCardHeader";
import { getRelatedId, sortByLabelFR, todayYYYYMMDD } from "./helpers";
import type { QualificationCardProps, RowVM } from "./types";

export function QualificationCard({
  title,
  mode,
  qualifications,
  loadOptions,
  disabled = false,
  onAdd,
  onUpdateDate,
  onDelete,
  confirmDelete,
}: QualificationCardProps) {
  const [options, setOptions] = useState<{ id: number; label: string }[]>([]);
  const [optLoading, setOptLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Add panel state
  const [addOpen, setAddOpen] = useState(false);
  const [addRelatedId, setAddRelatedId] = useState<number | "">("");
  const [addDate, setAddDate] = useState<string>(todayYYYYMMDD());

  // Which row is currently being edited (locks other interactions)
  const [editingId, setEditingId] = useState<number | null>(null);

  const entityLabel = mode === "agent" ? "Poste" : "Agent";

  const lockAdd = disabled || optLoading || editingId !== null;
  const lockRows = disabled || addOpen;

  // Load select options (postes / agents)
  useEffect(() => {
    let cancelled = false;

    async function run() {
      setOptLoading(true);
      setError(null);
      try {
        const opts = await loadOptions();
        if (!cancelled) setOptions(opts);
      } catch (e: any) {
        if (!cancelled) setError(e?.message ?? "Impossible de charger les options.");
      } finally {
        if (!cancelled) setOptLoading(false);
      }
    }

    run();
    return () => {
      cancelled = true;
    };
  }, [loadOptions]);

  const alreadyLinked = useMemo(() => {
    const s = new Set<number>();
    for (const q of qualifications) s.add(getRelatedId(mode, q));
    return s;
  }, [mode, qualifications]);

  const optionsById = useMemo(() => {
    const m = new Map<number, string>();
    for (const o of options) m.set(o.id, o.label);
    return m;
  }, [options]);

  const availableOptions = useMemo(() => {
    const filtered = options.filter((o) => !alreadyLinked.has(o.id));
    return sortByLabelFR(filtered.slice());
  }, [options, alreadyLinked]);

  const rows: RowVM[] = useMemo(() => {
    const computed = qualifications.map((q) => {
      const relatedId = getRelatedId(mode, q);
      const label = optionsById.get(relatedId) ?? `${entityLabel} #${relatedId}`;
      return { relatedId, label, date: q.date_qualification ?? "" };
    });

    computed.sort(
      (a, b) => a.label.localeCompare(b.label, "fr") || a.relatedId - b.relatedId
    );
    return computed;
  }, [qualifications, mode, optionsById, entityLabel]);

  // Auto-select first available option when opening the add panel
  useEffect(() => {
    if (!addOpen) return;
    if (addRelatedId !== "") return;
    if (availableOptions.length === 0) return;
    setAddRelatedId(availableOptions[0]!.id);
  }, [addOpen, addRelatedId, availableOptions]);

  async function handleAdd() {
    if (disabled) return;
    if (addRelatedId === "" || !addDate) return;

    setError(null);
    try {
      await onAdd({ related_id: addRelatedId, date_qualification: addDate });
      setAddOpen(false);
      setAddRelatedId("");
      setAddDate(todayYYYYMMDD());
    } catch (e: any) {
      setError(
        e?.message ?? `Impossible d’ajouter un(e) ${entityLabel.toLowerCase()}.`
      );
    }
  }

  async function handleDelete(relatedId: number, label: string) {
    if (disabled) return;

    const ok = await confirmDelete(label);
    if (!ok) return;

    setError(null);
    try {
      await onDelete({ related_id: relatedId });
    } catch (e: any) {
      setError(e?.message ?? "Suppression impossible.");
    }
  }

  async function handleUpdateDate(relatedId: number, date_qualification: string) {
    if (disabled) return;

    setError(null);
    try {
      await onUpdateDate({ related_id: relatedId, date_qualification });
    } catch (e: any) {
      setError(e?.message ?? "Mise à jour impossible.");
      throw e; // Let the caller decide whether to keep the row in edit mode
    }
  }

  return (
    <Card>
      <CardHeader className="pb-3">
        <QualificationCardHeader
          title={title}
          mode={mode}
          count={rows.length}
          disabled={disabled}
          addDisabled={lockAdd}
          onToggleAdd={() => {
            // Opening add panel cancels any active edit to avoid conflicting states
            setEditingId(null);
            setAddOpen((v) => !v);
          }}
        />
      </CardHeader>

      <CardContent className="space-y-4">
        {error ? (
          <Alert variant="destructive">
            <AlertTitle>Erreur</AlertTitle>
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        ) : null}

        {rows.length === 0 ? (
          <div className="text-sm text-muted-foreground">Aucune qualification.</div>
        ) : (
          <div className="space-y-2">
            {rows.map((r) => (
              <QualificationRow
                key={r.relatedId}
                label={r.label}
                dateYYYYMMDD={r.date}
                disabled={disabled}
                locked={lockRows || (editingId !== null && editingId !== r.relatedId)}
                isEditing={editingId === r.relatedId}
                onStartEdit={() => {
                  // Starting an edit closes the add panel to avoid conflicting states
                  setAddOpen(false);
                  setEditingId(r.relatedId);
                }}
                onCancelEdit={() => setEditingId(null)}
                onDelete={() => handleDelete(r.relatedId, r.label)}
                onSaveDate={async (d) => {
                  try {
                    await handleUpdateDate(r.relatedId, d);
                    setEditingId(null);
                  } catch {
                    // Keep edit mode open if update failed
                  }
                }}
              />
            ))}
          </div>
        )}

        {addOpen ? (
          <AddQualificationPanel
            entityLabel={entityLabel}
            disabled={disabled}
            optLoading={optLoading}
            availableOptions={availableOptions}
            addRelatedId={addRelatedId}
            addDate={addDate}
            onChangeRelatedId={setAddRelatedId}
            onChangeDate={setAddDate}
            onCancel={() => {
              setAddOpen(false);
              setAddRelatedId("");
              setAddDate(todayYYYYMMDD());
            }}
            onSubmit={handleAdd}
          />
        ) : null}
      </CardContent>
    </Card>
  );
}
