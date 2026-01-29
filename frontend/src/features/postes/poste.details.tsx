"use client";

import { useCallback, useEffect, useState } from "react";
import type { PosteDetail, Qualification, Tranche } from "@/types";

import { QualificationCard } from "@/components/admin/QualificationCard";
import { TranchesCard } from "@/components/admin/TranchesCard";

import { listAgents } from "@/services/agents.service";
import {
  createQualification,
  updateQualification,
  deleteQualification,
} from "@/services/qualifications.service";
import {
  createTranche,
  patchTranche,
  removeTranche,
} from "@/services/tranches.service";

import type { ConfirmOptions } from "@/hooks/useConfirm";
import { PosteHeaderCard } from "@/features/postes/cards/PosteHeaderCard";
import { PosteCoverageCard } from "./cards/PosteCoverageCard";

export default function PosteDetails({
  poste,
  confirm,
}: {
  poste: PosteDetail;
  confirm: (opts: ConfirmOptions) => Promise<boolean>;
}) {
  const [tranches, setTranches] = useState<Tranche[]>(poste.tranches ?? []);
  useEffect(() => setTranches(poste.tranches ?? []), [poste.tranches]);

  const [qualifications, setQualifications] = useState<Qualification[]>(
    poste.qualifications ?? []
  );
  useEffect(
    () => setQualifications(poste.qualifications ?? []),
    [poste.qualifications]
  );

  const [busyQualifications, setBusyQualifications] = useState(false);
  const [busyTranches, setBusyTranches] = useState(false);

  // ------------------------
  // Qualifications
  // ------------------------
  async function onAdd(payload: { related_id: number; date_qualification: string }) {
    setBusyQualifications(true);
    try {
      const created = await createQualification({
        agent_id: payload.related_id,
        poste_id: poste.id,
        date_qualification: payload.date_qualification,
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
    try {
      const updated = await updateQualification(payload.related_id, poste.id, {
        date_qualification: payload.date_qualification,
      });

      setQualifications((prev) =>
        prev.map((q) =>
          q.agent_id === payload.related_id
            ? { ...q, date_qualification: updated.date_qualification }
            : q
        )
      );
    } finally {
      setBusyQualifications(false);
    }
  }

  async function onDelete(payload: { related_id: number }) {
    setBusyQualifications(true);
    try {
      await deleteQualification(payload.related_id, poste.id);
      setQualifications((prev) => prev.filter((q) => q.agent_id !== payload.related_id));
    } finally {
      setBusyQualifications(false);
    }
  }

  const loadAgentOptions = useCallback(async () => {
    const res = await listAgents({ page: 1, page_size: 200 });
    return res.items.map((a) => ({ id: a.id, label: `${a.nom} ${a.prenom}` }));
  }, []);

  // ------------------------
  // Tranches
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

      setTranches((prev) => [...prev, created]);
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
      const updated = await patchTranche(trancheId, payload);
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
      <PosteHeaderCard
        poste={poste}
        tranchesCount={tranches.length}
        qualificationsCount={qualifications.length}
      />

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

      <PosteCoverageCard
        posteId={poste.id}
        tranches={tranches}
        disabled={busyTranches || busyQualifications}
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
    </div>
  );
}
