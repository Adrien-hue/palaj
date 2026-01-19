"use client";

import { useEffect, useMemo, useState } from "react";
import { Button, SecondaryButton } from "@/components/ui";
import { AdminDetailsCard } from "@/components/admin/AdminDetailsCard";
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

  const [draftId, setDraftId] = useState<number | "">(initialId ?? "");
  const [selectedHint, setSelectedHint] = useState<string | null>(
    normalizeDesc(regime?.desc)
  );

  // When parent regime changes (after save), sync draft if not editing
  useEffect(() => {
    if (editing) return;
    setDraftId(initialId ?? "");
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
        if (!cancelled)
          setError(e?.message ?? "Impossible de charger les régimes.");
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
    const cur = initialId ?? "";
    return draftId !== cur;
  }, [draftId, initialId]);

  const canSave = editing && canEdit && draftId !== "" && isDirty;

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
    setDraftId(initialId ?? "");
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
      setDraftId("");
      setSelectedHint(null);
    } catch (e: any) {
      setError(e?.message ?? "Suppression impossible.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <AdminDetailsCard title={title}>
      {/* Summary */}
      {regime ? (
        <div>
          <AdminDetailsRow label="Nom" value={regime.nom} />
          <AdminDetailsRow label="Description" value={regime.desc || "—"} />
        </div>
      ) : (
        <div className="text-sm text-zinc-600">Aucun régime.</div>
      )}

      {error ? <div className="mt-3 text-sm text-red-600">{error}</div> : null}

      {!editing ? (
        <div className="mt-3 flex justify-end">
          <SecondaryButton
            type="button"
            size="compact"
            onClick={() => {
              if (!canEdit) return;
              setEditing(true);

              // Preselect first option if none
              if (draftId === "" && options.length > 0) {
                setDraftId(options[0].id);
                setSelectedHint(options[0].hint ?? null);
              }
            }}
            disabled={!canEdit || optLoading}
          >
            Modifier
          </SecondaryButton>
        </div>
      ) : (
        <div className="mt-3 rounded-xl bg-zinc-50 p-3 ring-1 ring-zinc-200">
          <div className="text-xs font-medium text-zinc-700">
            Choisir un régime
          </div>

          <div className="mt-2">
            <select
              className="w-full rounded-lg border border-zinc-200 bg-white px-2 py-2 text-sm"
              value={draftId}
              onChange={(e) => {
                const v = e.target.value ? Number(e.target.value) : "";
                setDraftId(v);

                if (v !== "") {
                  const opt = optionById.get(v);
                  setSelectedHint(opt?.hint ?? null);
                } else {
                  setSelectedHint(null);
                }
              }}
              disabled={locked || optLoading}
              title={selectedHint ?? undefined}
            >
              {options.map((o) => (
                <option key={o.id} value={o.id}>
                  {o.label}
                </option>
              ))}
            </select>

            {selectedHint ? (
              <div className="mt-1 text-xs text-zinc-600">{selectedHint}</div>
            ) : (
              <div className="mt-1 text-xs text-zinc-500">—</div>
            )}
          </div>

          {/* Footer actions (consistent with other cards/forms) */}
          <div className="mt-3 flex items-center justify-between gap-2">
            <Button
              type="button"
              variant="dangerSoft"
              size="compact"
              onClick={handleClear}
              disabled={locked || !regime}
              title={!regime ? "Aucun régime à retirer" : "Retirer le régime"}
            >
              Retirer
            </Button>

            <div className="flex items-center gap-2">
              <SecondaryButton
                type="button"
                size="compact"
                onClick={handleCancel}
                disabled={locked}
              >
                Annuler
              </SecondaryButton>

              <Button
                type="button"
                variant="success"
                size="compact"
                onClick={handleSave}
                disabled={!canSave}
                loading={busy}
              >
                Enregistrer
              </Button>
            </div>
          </div>
        </div>
      )}

      {optLoading ? (
        <div className="mt-2 text-xs text-zinc-600">Chargement…</div>
      ) : null}
    </AdminDetailsCard>
  );
}
