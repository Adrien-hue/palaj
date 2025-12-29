"use client";

import { useCallback, useState } from "react";
import type { Agent } from "@/types";
import {
  activateAgent,
  createAgent,
  deactivateAgent,
  getAgent,
  patchAgent,
  removeAgent,
} from "@/services/agents.service";
import { buildAgentPatch, type AgentFormSubmitValues } from "@/features/agents/buildAgentPatch";

export type ConfirmFn = (opts: {
  title: string;
  description?: string;
  confirmText?: string;
  cancelText?: string;
  variant?: "danger" | "default";
}) => Promise<boolean>;

export type ShowToastFn = (t: {
  type: "success" | "error" | "info";
  title: string;
  message?: string;
  durationMs?: number;
}) => void;

export function useAgentsCrud(opts: {
  confirm: ConfirmFn;
  showToast: ShowToastFn;
  refresh: () => void;
}) {
  const { confirm, showToast, refresh } = opts;

  const [editLoadingId, setEditLoadingId] = useState<number | null>(null);

  const [modalOpen, setModalOpen] = useState(false);
  const [modalMode, setModalMode] = useState<"create" | "edit">("create");
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const [togglingIds, setTogglingIds] = useState<Set<number>>(new Set());

  const openCreate = useCallback(() => {
    setSelectedAgent(null);
    setModalMode("create");
    setModalOpen(true);
  }, []);

  const closeModal = useCallback(() => {
    if (submitting) return;
    setModalOpen(false);
  }, [submitting]);

  const openEdit = useCallback(
    async (a: Agent) => {
      if (editLoadingId === a.id) return;

      setEditLoadingId(a.id);
      try {
        const full = await getAgent(a.id);
        setSelectedAgent(full);
        setModalMode("edit");
        setModalOpen(true);
      } catch (e) {
        showToast({
          type: "error",
          title: "Chargement impossible",
          message: e instanceof Error ? e.message : "Erreur inconnue",
          durationMs: 6000,
        });
      } finally {
        setEditLoadingId(null);
      }
    },
    [editLoadingId, showToast]
  );

  const deleteAgent = useCallback(
    async (a: Agent) => {
      const ok = await confirm({
        title: "Supprimer l'agent",
        description: `Confirmer la suppression de ${a.nom} ${a.prenom} ?`,
        confirmText: "Supprimer",
        cancelText: "Annuler",
        variant: "danger",
      });
      if (!ok) return;

      try {
        await removeAgent(a.id);
        showToast({
          type: "success",
          title: "Agent supprimé",
          message: `${a.nom} ${a.prenom} a été supprimé.`,
        });
        refresh();
      } catch (e) {
        showToast({
          type: "error",
          title: "Suppression impossible",
          message: e instanceof Error ? e.message : "Erreur inconnue",
          durationMs: 6000,
        });
      }
    },
    [confirm, refresh, showToast]
  );

  const toggleActive = useCallback(
    async (a: Agent) => {
      if (a.actif) {
        const ok = await confirm({
          title: "Désactiver l'agent",
          description: `Confirmer la désactivation de ${a.nom} ${a.prenom} ?`,
          confirmText: "Désactiver",
          cancelText: "Annuler",
          variant: "danger",
        });
        if (!ok) return;
      }

      setTogglingIds((prev) => new Set(prev).add(a.id));
      try {
        if (a.actif) {
          await deactivateAgent(a.id);
        } else {
          await activateAgent(a.id);
        }

        showToast({
          type: "success",
          title: a.actif ? "Agent désactivé" : "Agent activé",
          message: `${a.nom} ${a.prenom} est maintenant ${a.actif ? "inactif" : "actif"}.`,
        });

        refresh();
      } catch (e) {
        showToast({
          type: "error",
          title: "Action impossible",
          message: e instanceof Error ? e.message : "Erreur inconnue",
          durationMs: 6000,
        });
      } finally {
        setTogglingIds((prev) => {
          const next = new Set(prev);
          next.delete(a.id);
          return next;
        });
      }
    },
    [confirm, refresh, showToast]
  );

  const submitForm = useCallback(
    async (values: AgentFormSubmitValues) => {
      setSubmitting(true);
      try {
        if (modalMode === "create") {
          await createAgent({
            nom: values.nom,
            prenom: values.prenom,
            code_personnel: values.code_personnel,
            regime_id: values.regime_id,
            actif: true,
          });

          showToast({ type: "success", title: "Agent créé" });
        } else {
          if (!selectedAgent) return;

          const patch = buildAgentPatch(selectedAgent, values);
          await patchAgent(selectedAgent.id, patch as any);

          showToast({ type: "success", title: "Agent mis à jour" });
        }

        setModalOpen(false);
        refresh();
      } catch (e) {
        showToast({
          type: "error",
          title: "Enregistrement impossible",
          message: e instanceof Error ? e.message : "Erreur inconnue",
          durationMs: 6000,
        });
      } finally {
        setSubmitting(false);
      }
    },
    [modalMode, refresh, selectedAgent, showToast]
  );

  return {
    // state
    editLoadingId,
    modalOpen,
    modalMode,
    selectedAgent,
    submitting,
    togglingIds,

    // actions
    openCreate,
    openEdit,
    closeModal,
    deleteAgent,
    toggleActive,
    submitForm,
  };
}
