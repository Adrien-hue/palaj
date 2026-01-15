"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import type { PosteDetail, Qualification } from "@/types";

import { QualificationCard } from "@/components/admin/QualificationCard";

import { listAgents } from "@/services/agents.service";
import {
  createQualification,
  updateQualification,
  deleteQualification,
} from "@/services/qualifications.service";
import ConfirmDialog from "@/components/admin/dialogs/ConfirmDialog";

function formatTime(t: string) {
  return t?.slice(0, 5) ?? "—";
}

type ConfirmState = {
  open: boolean;
  title: string;
  description?: string;
  confirmText?: string;
  cancelText?: string;
  variant?: "danger" | "default";
  resolve?: (value: boolean) => void;
};

function useConfirm() {
  const [state, setState] = useState<ConfirmState>({ open: false, title: "" });
  const resolveRef = useRef<ConfirmState["resolve"]>(undefined);

  function confirm(opts: Omit<ConfirmState, "open" | "resolve">) {
    return new Promise<boolean>((resolve) => {
      resolveRef.current = resolve;
      setState({
        open: true,
        title: opts.title,
        description: opts.description,
        confirmText: opts.confirmText,
        cancelText: opts.cancelText,
        variant: opts.variant,
      });
    });
  }

  function close(value: boolean) {
    resolveRef.current?.(value);
    resolveRef.current = undefined;
    setState({ open: false, title: "" });
  }

  const dialog = (
    <ConfirmDialog
      open={state.open}
      title={state.title}
      description={state.description}
      confirmText={state.confirmText}
      cancelText={state.cancelText}
      variant={state.variant}
      onConfirm={() => close(true)}
      onCancel={() => close(false)}
    />
  );

  return { confirm, dialog };
}

export default function PosteDetails({ poste }: { poste: PosteDetail }) {
  const tranches = poste.tranches ?? [];

  const [qualifications, setQualifications] = useState<Qualification[]>(poste.qualifications ?? []);
  useEffect(() => setQualifications(poste.qualifications ?? []), [poste.qualifications]);

  const [busy, setBusy] = useState(false);
  const { confirm, dialog: confirmDialogNode } = useConfirm();

  async function onAdd(payload: { related_id: number; date_qualification: string }) {
    setBusy(true);

    const agent_id = payload.related_id;
    const date_qualification = payload.date_qualification;

    try {
      const created = await createQualification({ agent_id: agent_id, poste_id: poste.id, date_qualification: date_qualification });
      
      setQualifications((prev) => {
        const next = prev.filter((q) => q.agent_id !== created.agent_id);
        next.push(created);
        return next;
      });
    } finally {
      setBusy(false);
    }
  }

  async function onUpdateDate(payload: { related_id: number; date_qualification: string }) {
    setBusy(true);

    const agent_id = payload.related_id;
    const date_qualification = payload.date_qualification;
    
    try {
      const updated = await updateQualification(agent_id, poste.id, {
        date_qualification: date_qualification,
      });

      setQualifications((prev) =>
        prev.map((q) => (q.agent_id === agent_id ? { ...q, date_qualification: updated.date_qualification } : q))
      );
    } finally {
      setBusy(false);
    }
  }

  async function onDelete(payload: { related_id: number }) {
    setBusy(true);

    const agent_id = payload.related_id;

    try {
      await deleteQualification(agent_id, poste.id);
      setQualifications((prev) => prev.filter((q) => q.agent_id !== agent_id));
    } finally {
      setBusy(false);
    }
  }

  const loadAgentOptions = useCallback(async () => {
    const res = await listAgents({ page: 1, page_size: 200 });
    return res.items.map((a) => ({ id: a.id, label: `${a.nom} ${a.prenom}` }));
  }, []);

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="rounded-2xl bg-zinc-50 p-4 ring-1 ring-zinc-200">
        <div className="text-base font-semibold text-zinc-900">{poste.nom}</div>
        <div className="mt-1 text-xs text-zinc-600">ID: {poste.id}</div>
      </div>

      {/* Résumé */}
      <div className="grid gap-3 sm:grid-cols-2">
        <div className="rounded-2xl bg-white p-4 ring-1 ring-zinc-200">
          <div className="text-sm font-semibold text-zinc-900">Tranches</div>
          <div className="mt-1 text-sm text-zinc-700">{tranches.length} au total</div>
          <div className="mt-1 text-xs text-zinc-500">Horaires associés à ce poste.</div>
        </div>

        <div className="rounded-2xl bg-white p-4 ring-1 ring-zinc-200">
          <div className="text-sm font-semibold text-zinc-900">Qualifications</div>
          <div className="mt-1 text-sm text-zinc-700">{qualifications.length} au total</div>
          <div className="mt-1 text-xs text-zinc-500">Agents qualifiés sur ce poste.</div>
        </div>
      </div>

      {/* Tranches */}
      <div className="rounded-2xl bg-white p-4 ring-1 ring-zinc-200">
        <div className="flex items-center justify-between gap-4">
          <div className="text-sm font-semibold text-zinc-900">Tranches</div>
          <div className="text-xs text-zinc-600">{tranches.length}</div>
        </div>

        {tranches.length === 0 ? (
          <div className="mt-2 text-sm text-zinc-600">Aucune tranche.</div>
        ) : (
          <div className="mt-3 space-y-2">
            {tranches.map((t) => (
              <div
                key={t.id}
                className="flex items-center justify-between gap-4 rounded-xl bg-zinc-50 px-3 py-2 ring-1 ring-zinc-100"
              >
                <div className="text-sm text-zinc-900">{t.nom}</div>
                <div className="text-xs text-zinc-600">
                  {formatTime(t.heure_debut)} → {formatTime(t.heure_fin)}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <QualificationCard
        title="Qualifications"
        mode="poste"
        qualifications={qualifications}
        loadOptions={loadAgentOptions}
        disabled={busy}
        onAdd={onAdd}
        onUpdateDate={onUpdateDate}
        onDelete={onDelete}
        confirmDelete={(label) =>
          confirm({
            title: "Supprimer une qualification",
            description: `Supprimer "${label}" ?`,
            confirmText: "Supprimer",
            cancelText: "Annuler",
            variant: "danger",
          })
        }
      />

      {confirmDialogNode}
    </div>
  );
}
