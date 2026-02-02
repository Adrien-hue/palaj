"use client";

import { useMemo, useRef, useState } from "react";

import { Card, CardContent } from "@/components/ui/card";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";

import TranchesCardHeader from "./TranchesCardHeader";
import AddTranchePanel from "./AddTranchePanel";
import TrancheRow from "./TrancheRow";
import TranchesTimeline from "./TranchesTimeline";

import { toApiTime, toTimeInput } from "./helpers";
import type { TrancheDraft, TranchesCardProps } from "./types";

const EMPTY_DRAFT: TrancheDraft = { nom: "", heure_debut: "", heure_fin: "" };

export function TranchesCard({
  title,
  tranches,
  disabled = false,
  onAdd,
  onUpdate,
  onDelete,
  confirmDelete,
}: TranchesCardProps) {
  const [error, setError] = useState<string | null>(null);
  const [addOpen, setAddOpen] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [listOpen, setListOpen] = useState(false);
  const [selectedId, setSelectedId] = useState<number | null>(null);

  const [addDraft, setAddDraft] = useState<TrancheDraft>(EMPTY_DRAFT);

  const listContainerRef = useRef<HTMLDivElement | null>(null);
  const rowRefs = useRef<Record<number, HTMLDivElement | null>>({});

  const lockAdd = disabled || editingId !== null;
  const lockRows = disabled || addOpen;

  const rows = useMemo(() => {
    return tranches
      .slice()
      .sort((a, b) => a.nom.localeCompare(b.nom, "fr") || a.id - b.id)
      .map((t) => ({
        id: t.id,
        nom: t.nom,
        heure_debut: toTimeInput(t.heure_debut),
        heure_fin: toTimeInput(t.heure_fin),
        color: t.color,
      }));
  }, [tranches]);

  const hasRows = rows.length > 0;

  function resetAddForm() {
    setAddDraft(EMPTY_DRAFT);
  }

  function closeAdd() {
    setAddOpen(false);
    resetAddForm();
  }

  async function handleAdd() {
    if (disabled) return;

    const nom = addDraft.nom.trim();
    if (!nom || !addDraft.heure_debut || !addDraft.heure_fin) return;

    setError(null);
    try {
      await onAdd({
        nom,
        heure_debut: toApiTime(addDraft.heure_debut),
        heure_fin: toApiTime(addDraft.heure_fin),
      });
      closeAdd();
    } catch (e: any) {
      setError(e?.message ?? "Impossible d’ajouter la tranche.");
    }
  }

  async function handleDelete(id: number, label: string) {
    if (disabled) return;

    const ok = await confirmDelete(label);
    if (!ok) return;

    setError(null);
    try {
      await onDelete(id);
      setSelectedId((cur) => (cur === id ? null : cur));
      if (editingId === id) setEditingId(null);
    } catch (e: any) {
      setError(e?.message ?? "Impossible de supprimer la tranche.");
    }
  }

  async function handleUpdate(id: number, draft: TrancheDraft) {
    if (disabled) return;

    setError(null);
    try {
      await onUpdate(id, {
        nom: draft.nom.trim(),
        heure_debut: toApiTime(draft.heure_debut),
        heure_fin: toApiTime(draft.heure_fin),
        color: draft.color ?? null,
      });
    } catch (e: any) {
      setError(e?.message ?? "Impossible de mettre à jour la tranche.");
      throw e;
    }
  }

  function toggleAdd() {
    setListOpen(true);
    setEditingId(null);
    setSelectedId(null);

    setAddOpen((prev) => {
      const next = !prev;
      if (!next) resetAddForm(); // on ferme -> reset
      return next;
    });
  }

  function startEdit(id: number) {
    setListOpen(true);
    setSelectedId(id);

    setAddOpen(false);
    resetAddForm();
    setEditingId(id);
  }

  function cancelEdit() {
    setEditingId(null);
  }

  function selectFromTimeline(id: number) {
    setSelectedId(id);

    // Don’t disturb ongoing add/edit
    if (addOpen || editingId !== null) return;

    setListOpen(true);

    requestAnimationFrame(() => {
      listContainerRef.current?.scrollIntoView({
        behavior: "smooth",
        block: "nearest",
      });
      rowRefs.current[id]?.scrollIntoView({
        behavior: "smooth",
        block: "center",
      });
    });
  }

  const showListArea = listOpen && hasRows;
  const showAddInsideList = showListArea && addOpen;
  const showAddStandalone = (!showListArea && addOpen) || (!hasRows && addOpen);

  return (
    <Card>
      <TranchesCardHeader
        title={title}
        count={rows.length}
        disabled={disabled}
        addDisabled={lockAdd}
        onToggleAdd={toggleAdd}
        listOpen={listOpen}
        onToggleList={() => setListOpen((v) => !v)}
      />

      <CardContent className="space-y-4">
        {error ? (
          <Alert variant="destructive">
            <AlertTitle>Erreur</AlertTitle>
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        ) : null}

        <TranchesTimeline
          tranches={tranches}
          markerEveryHours={2}
          onSelectTranche={selectFromTimeline}
        />

        {!hasRows && !addOpen ? (
          <div className="text-sm text-muted-foreground">Aucune tranche.</div>
        ) : null}

        {showListArea ? (
          <div>
            <div
              ref={listContainerRef}
              className="max-h-[360px] overflow-auto rounded-xl border bg-background p-2"
            >
              <div className="space-y-2">
                {rows.map((r) => (
                  <div
                    key={r.id}
                    ref={(el) => {
                      rowRefs.current[r.id] = el;
                    }}
                    className={[
                      "rounded-xl",
                      selectedId === r.id
                        ? "ring-2 ring-ring ring-offset-2 ring-offset-background"
                        : "",
                    ].join(" ")}
                  >
                    <TrancheRow
                      id={r.id}
                      label={r.nom}
                      heure_debut={r.heure_debut}
                      heure_fin={r.heure_fin}
                      color={r.color}
                      disabled={disabled}
                      locked={lockRows || (editingId !== null && editingId !== r.id)}
                      isEditing={editingId === r.id}
                      onStartEdit={() => startEdit(r.id)}
                      onCancelEdit={cancelEdit}
                      onDelete={() => handleDelete(r.id, r.nom)}
                      onSave={async (draft) => {
                        try {
                          await handleUpdate(r.id, draft);
                          setEditingId(null);
                        } catch {
                          // keep editing open on error
                        }
                      }}
                    />
                  </div>
                ))}
              </div>

              {showAddInsideList ? (
                <div className="mt-3">
                  <AddTranchePanel
                    disabled={disabled}
                    draft={addDraft}
                    onChange={setAddDraft}
                    onCancel={closeAdd}
                    onSubmit={handleAdd}
                  />
                </div>
              ) : null}
            </div>

            <div className="mt-2 text-[11px] text-muted-foreground">
              Faites défiler pour voir plus de tranches.
            </div>
          </div>
        ) : null}

        {showAddStandalone ? (
          <AddTranchePanel
            disabled={disabled}
            draft={addDraft}
            onChange={setAddDraft}
            onCancel={closeAdd}
            onSubmit={handleAdd}
          />
        ) : null}
      </CardContent>
    </Card>
  );
}
