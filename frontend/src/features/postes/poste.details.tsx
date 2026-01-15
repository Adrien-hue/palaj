"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import type { PosteDetail, Qualification, Tranche } from "@/types";

import { QualificationCard } from "@/components/admin/QualificationCard";
import { TranchesCard } from "@/components/admin/TranchesCard";

import { listAgents } from "@/services/agents.service";
import { createQualification, updateQualification, deleteQualification } from "@/services/qualifications.service";
import { createTranche, patchTranche, removeTranche } from "@/services/tranches.service";

import ConfirmDialog from "@/components/admin/dialogs/ConfirmDialog";

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
  // ✅ Local state for tranches (source of truth for UI updates)
  const [tranches, setTranches] = useState<Tranche[]>(poste.tranches ?? []);
  useEffect(() => setTranches(poste.tranches ?? []), [poste.tranches]);

  const [qualifications, setQualifications] = useState<Qualification[]>(poste.qualifications ?? []);
  useEffect(() => setQualifications(poste.qualifications ?? []), [poste.qualifications]);

  // ✅ Separate busy states (avoid blocking unrelated sections)
  const [busyQualifications, setBusyQualifications] = useState(false);
  const [busyTranches, setBusyTranches] = useState(false);

  const { confirm, dialog: confirmDialogNode } = useConfirm();

  // ------------------------
  // Qualifications handlers
  // ------------------------
  async function onAdd(payload: { related_id: number; date_qualification: string }) {
    setBusyQualifications(true);

    const agent_id = payload.related_id;
    const date_qualification = payload.date_qualification;

    try {
      const created = await createQualification({
        agent_id,
        poste_id: poste.id,
        date_qualification,
      });

      setQualifications((prev) => {
        const next = prev.filter((q) => q.agent_id !== created.agent_id);
        next.push(created);
        return next;
      });
    } finally {
      setBusyQualifications(false);
    }
  }

  async function onUpdateDate(payload: { related_id: number; date_qualification: string }) {
    setBusyQualifications(true);

    const agent_id = payload.related_id;
    const date_qualification = payload.date_qualification;

    try {
      const updated = await updateQualification(agent_id, poste.id, { date_qualification });

      setQualifications((prev) =>
        prev.map((q) =>
          q.agent_id === agent_id ? { ...q, date_qualification: updated.date_qualification } : q
        )
      );
    } finally {
      setBusyQualifications(false);
    }
  }

  async function onDelete(payload: { related_id: number }) {
    setBusyQualifications(true);

    const agent_id = payload.related_id;

    try {
      await deleteQualification(agent_id, poste.id);
      setQualifications((prev) => prev.filter((q) => q.agent_id !== agent_id));
    } finally {
      setBusyQualifications(false);
    }
  }

  const loadAgentOptions = useCallback(async () => {
    const res = await listAgents({ page: 1, page_size: 200 });
    return res.items.map((a) => ({ id: a.id, label: `${a.nom} ${a.prenom}` }));
  }, []);

  // ------------------------
  // Tranches handlers
  // ------------------------
  async function onAddTranche(payload: { nom: string; heure_debut: string; heure_fin: string }) {
    setBusyTranches(true);

    try {
      const created = await createTranche({
        poste_id: poste.id,
        nom: payload.nom,
        heure_debut: payload.heure_debut,
        heure_fin: payload.heure_fin,
      });

      setTranches((prev) => {
        const next = prev.slice();
        next.push(created);
        return next;
      });
    } finally {
      setBusyTranches(false);
    }
  }

  async function onUpdateTranche(
    trancheId: number,
    payload: { nom: string; heure_debut: string; heure_fin: string }
  ) {
    setBusyTranches(true);

    try {
      const updated = await patchTranche(trancheId, {
        nom: payload.nom,
        heure_debut: payload.heure_debut,
        heure_fin: payload.heure_fin,
      });

      setTranches((prev) => prev.map((t) => (t.id === trancheId ? updated : t)));
    } finally {
      setBusyTranches(false);
    }
  }

  async function onDeleteTranche(trancheId: number) {
    setBusyTranches(true);

    try {
      await removeTranche(trancheId);
      setTranches((prev) => prev.filter((t) => t.id !== trancheId));
    } finally {
      setBusyTranches(false);
    }
  }

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

      <TranchesCard
        title="Tranches"
        tranches={tranches}
        disabled={busyTranches}
        onAdd={onAddTranche}
        onUpdate={onUpdateTranche}
        onDelete={onDeleteTranche}
        confirmDelete={(label) =>
          confirm({
            title: "Supprimer une tranche",
            description: `Supprimer "${label}" ?`,
            confirmText: "Supprimer",
            cancelText: "Annuler",
            variant: "danger",
          })
        }
      />

      <QualificationCard
        title="Qualifications"
        mode="poste"
        qualifications={qualifications}
        loadOptions={loadAgentOptions}
        disabled={busyQualifications}
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
