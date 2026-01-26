"use client";

import { useCallback, useState } from "react";
import { toast } from "sonner";

import type { Agent, AgentDetails } from "@/types";
import {
  activateAgent,
  createAgent,
  deactivateAgent,
  getAgent,
  patchAgent,
  removeAgent,
} from "@/services/agents.service";
import {
  buildAgentPatch,
  type AgentFormSubmitValues,
} from "@/features/agents/buildAgentPatch";

import type { ConfirmOptions } from "@/hooks/useConfirm";

export type ConfirmFn = (opts: ConfirmOptions) => Promise<boolean>;

export function useAgentsCrud(opts: { confirm: ConfirmFn; refresh: () => void }) {
  const { confirm, refresh } = opts;

  const [editLoadingId, setEditLoadingId] = useState<number | null>(null);

  const [detailsOpen, setDetailsOpen] = useState(false);
  const [detailsAgent, setDetailsAgent] = useState<AgentDetails | null>(null);
  const [viewLoadingId, setViewLoadingId] = useState<number | null>(null);

  const [modalOpen, setModalOpen] = useState(false);
  const [modalMode, setModalMode] = useState<"create" | "edit">("create");
  const [selectedAgent, setSelectedAgent] = useState<AgentDetails | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const [togglingIds, setTogglingIds] = useState<Set<number>>(new Set());

  const closeView = useCallback(() => {
    setDetailsOpen(false);
  }, []);

  const openView = useCallback(
    async (a: Agent) => {
      if (viewLoadingId === a.id) return;

      setViewLoadingId(a.id);
      try {
        const full = await getAgent(a.id);
        setDetailsAgent(full);
        setDetailsOpen(true);
      } catch (e) {
        toast.error("Chargement impossible", {
          description: e instanceof Error ? e.message : "Erreur inconnue",
        });
      } finally {
        setViewLoadingId(null);
      }
    },
    [viewLoadingId]
  );

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
        toast.error("Chargement impossible", {
          description: e instanceof Error ? e.message : "Erreur inconnue",
        });
      } finally {
        setEditLoadingId(null);
      }
    },
    [editLoadingId]
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
        toast.success("Agent supprimé", {
          description: `${a.nom} ${a.prenom} a été supprimé.`,
        });
        refresh();
      } catch (e) {
        toast.error("Suppression impossible", {
          description: e instanceof Error ? e.message : "Erreur inconnue",
        });
      }
    },
    [confirm, refresh]
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
        if (a.actif) await deactivateAgent(a.id);
        else await activateAgent(a.id);

        toast.success(a.actif ? "Agent désactivé" : "Agent activé", {
          description: `${a.nom} ${a.prenom} est maintenant ${
            a.actif ? "inactif" : "actif"
          }.`,
        });

        refresh();
      } catch (e) {
        toast.error("Action impossible", {
          description: e instanceof Error ? e.message : "Erreur inconnue",
        });
      } finally {
        setTogglingIds((prev) => {
          const next = new Set(prev);
          next.delete(a.id);
          return next;
        });
      }
    },
    [confirm, refresh]
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
          toast.success("Agent créé");
        } else {
          if (!selectedAgent) return;

          const patch = buildAgentPatch(selectedAgent, values);
          await patchAgent(selectedAgent.id, patch as any);

          toast.success("Agent mis à jour");
        }

        setModalOpen(false);
        refresh();
      } catch (e) {
        toast.error("Enregistrement impossible", {
          description: e instanceof Error ? e.message : "Erreur inconnue",
        });
      } finally {
        setSubmitting(false);
      }
    },
    [modalMode, refresh, selectedAgent]
  );

  return {
    // state
    detailsOpen,
    detailsAgent,
    viewLoadingId,
    editLoadingId,
    modalOpen,
    modalMode,
    selectedAgent,
    submitting,
    togglingIds,

    // actions
    openView,
    closeView,
    openCreate,
    openEdit,
    closeModal,
    deleteAgent,
    toggleActive,
    submitForm,
  };
}
