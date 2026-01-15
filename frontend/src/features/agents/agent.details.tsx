"use client";

import { useEffect, useRef, useState } from "react";
import type { AgentDetails as AgentDetailsType, Poste, Qualification } from "@/types";
import { getAgent, listPostes } from "@/services";
import { AgentHeaderCard } from "./cards/AgentHeaderCard";
import { AgentRegimeCard } from "./cards/AgentRegimeCard";
import { QualificationCard } from "@/components/admin/QualificationCard";
import ConfirmDialog from "@/components/admin/dialogs/ConfirmDialog";
import { createQualification, deleteQualification, updateQualification } from "@/services/qualifications.service";

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

export default function AgentDetails({ agent }: { agent: AgentDetailsType }) {
  const [qualifications, setQualifications] = useState<Qualification[]>(agent.qualifications ?? []);
  useEffect(() => setQualifications(agent.qualifications ?? []), [agent.qualifications]);

  const [busy, setBusy] = useState(false);
  const { confirm, dialog: confirmDialogNode } = useConfirm();
  
  async function onAdd(payload: { related_id: number; date_qualification: string }) {
    setBusy(true);

    const poste_id = payload.related_id;
    const date_qualification = payload.date_qualification;

    try {
      const created = await createQualification({ agent_id: agent.id, poste_id: poste_id, date_qualification: date_qualification });
      
      setQualifications((prev) => {
        const next = prev.filter((q) => q.poste_id !== created.poste_id);
        next.push(created);
        return next;
      });
    } finally {
      setBusy(false);
    }
  }

  async function onUpdateDate(payload: { related_id: number; date_qualification: string }) {
    setBusy(true);

    const poste_id = payload.related_id;
    const date_qualification = payload.date_qualification;
    
    try {
      const updated = await updateQualification(agent.id, payload.related_id, {
        date_qualification: payload.date_qualification,
      });

      setQualifications((prev) => prev.map((q) => (q.poste_id === payload.related_id ? updated : q)));
    } finally {
      setBusy(false);
    }
  }

  async function onDelete(payload: { related_id: number }) {
    setBusy(true);

    const poste_id = payload.related_id;

    try {
      await deleteQualification(agent.id, payload.related_id);
    setQualifications((prev) => prev.filter((q) => q.poste_id !== payload.related_id));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-4">
      <AgentHeaderCard agent={agent} />
      <AgentRegimeCard agent={agent} />

      <QualificationCard
        title="Qualifications"
        mode="agent"
        qualifications={qualifications}
        loadOptions={async () => {
          const res = await listPostes({ page: 1, page_size: 200 });
          return res.items.map((p) => ({ id: p.id, label: p.nom }));
        }}
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
