// frontend/src/components/admin/TranchesCard/TranchesCard.tsx
"use client";

import { useMemo, useRef, useState } from "react";
import CardHeader from "./CardHeader";
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
  // ---- UI state
  const [error, setError] = useState<string | null>(null);
  const [addOpen, setAddOpen] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [listOpen, setListOpen] = useState(true);
  const [selectedId, setSelectedId] = useState<number | null>(null);

  // Keep "Add" form state local to the card
  const [addDraft, setAddDraft] = useState<TrancheDraft>(EMPTY_DRAFT);

  // Refs used to scroll to a row after selecting from the timeline
  const listContainerRef = useRef<HTMLDivElement | null>(null);
  const rowRefs = useRef<Record<number, HTMLDivElement | null>>({});

  // ---- Locks
  // Don't allow opening "Add" while editing a row
  const lockAdd = disabled || editingId !== null;
  // Don't allow editing / deleting rows while "Add" panel is open
  const lockRows = disabled || addOpen;

  // ---- Derived rows for the editable list
  const rows = useMemo(() => {
    return tranches
      .slice()
      .sort((a, b) => a.nom.localeCompare(b.nom, "fr") || a.id - b.id)
      .map((t) => ({
        id: t.id,
        nom: t.nom,
        heure_debut: toTimeInput(t.heure_debut), // "HH:MM"
        heure_fin: toTimeInput(t.heure_fin), // "HH:MM"
      }));
  }, [tranches]);

  const hasRows = rows.length > 0;

  // ---- Helpers
  function resetAddForm() {
    setAddDraft(EMPTY_DRAFT);
  }

  function closeAdd() {
    setAddOpen(false);
    resetAddForm();
  }

  // ---- Actions
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
      setError(e?.message ?? "Failed to add tranche.");
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
      setError(e?.message ?? "Failed to delete tranche.");
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
      });
    } catch (e: any) {
      setError(e?.message ?? "Failed to update tranche.");
      throw e;
    }
  }

  function openAdd() {
    // Keep list open so we always have a safe scroll area (prevents page overflow)
    setListOpen(true);
    // Add mode and edit mode are mutually exclusive
    setEditingId(null);
    // Clear selection so the highlight doesn't feel "stuck"
    setSelectedId(null);

    setAddOpen((v) => !v);
    if (addOpen) resetAddForm();
  }

  function startEdit(id: number) {
    setListOpen(true);
    setSelectedId(id);

    // Edit mode and add mode are mutually exclusive
    setAddOpen(false);
    setEditingId(id);
  }

  function cancelEdit() {
    setEditingId(null);
  }

  function selectFromTimeline(id: number) {
    setSelectedId(id);

    // Don't disrupt an ongoing add/edit; only focus/scroll when the UI is idle
    if (addOpen || editingId !== null) return;

    setListOpen(true);

    requestAnimationFrame(() => {
      listContainerRef.current?.scrollIntoView({ behavior: "smooth", block: "nearest" });
      rowRefs.current[id]?.scrollIntoView({ behavior: "smooth", block: "center" });
    });
  }

  const showListArea = listOpen && hasRows;
  const showAddInsideList = showListArea && addOpen;
  const showAddStandalone = (!showListArea && addOpen) || (!hasRows && addOpen);

  return (
    <div className="rounded-2xl bg-white p-4 ring-1 ring-zinc-200">
      <CardHeader
        title={title}
        count={rows.length}
        disabled={disabled}
        addDisabled={lockAdd}
        onToggleAdd={openAdd}
        listOpen={listOpen}
        onToggleList={() => setListOpen((v) => !v)}
      />

      {error ? <div className="mt-2 text-sm text-red-600">{error}</div> : null}

      {/* Visual, read-only view (click -> focus row in list) */}
      <TranchesTimeline tranches={tranches} markerEveryHours={2} onSelectTranche={selectFromTimeline} />

      {/* Empty state (when list is open but there are no rows) */}
      {!hasRows && !addOpen ? (
        <div className="mt-3 text-sm text-zinc-600">Aucune tranche.</div>
      ) : null}

      {/* Scrollable list area */}
      {showListArea ? (
        <div className="mt-3">
          <div
            ref={listContainerRef}
            className="max-h-[360px] overflow-auto rounded-xl bg-white p-2 ring-1 ring-zinc-200"
          >
            <div className="space-y-2">
              {rows.map((r) => (
                <div
                  key={r.id}
                  ref={(el) => {
                    rowRefs.current[r.id] = el;
                  }}
                  className={["rounded-xl", selectedId === r.id ? "ring-2 ring-zinc-400" : ""].join(" ")}
                >
                  <TrancheRow
                    id={r.id}
                    label={r.nom}
                    heure_debut={r.heure_debut}
                    heure_fin={r.heure_fin}
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

            {/* Keep Add panel inside scrollable container to avoid page overflow */}
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

          <div className="mt-2 text-[11px] text-zinc-500">Faites défiler pour voir plus de tranches.</div>
        </div>
      ) : null}

      {/* If the list is hidden or empty but Add is open, show Add panel below */}
      {showAddStandalone ? (
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
  );
}
