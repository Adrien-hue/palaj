"use client";

import { useCallback, useState } from "react";
import { toast } from "sonner";

import type { Team, TeamBase } from "@/types";
import { createTeam, getTeam, updateTeam, removeTeam } from "@/services/teams.service";
import { buildTeamPatch } from "./buildTeamPatch";

import type { ConfirmOptions } from "@/hooks/useConfirm";

export type ConfirmFn = (opts: ConfirmOptions) => Promise<boolean>;

export function useTeamCrud(opts: {
  confirm: ConfirmFn;
  refresh: () => void;
}) {
  const { confirm, refresh } = opts;

  const [detailsOpen, setDetailsOpen] = useState(false);
  const [detailsTeam, setDetailsTeam] = useState<Team | null>(null);
  const [viewLoadingId, setViewLoadingId] = useState<number | null>(null);

  const [modalOpen, setModalOpen] = useState(false);
  const [modalMode, setModalMode] = useState<"create" | "edit">("create");
  const [selectedTeam, setSelectedTeam] = useState<Team | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const [editLoadingId, setEditLoadingId] = useState<number | null>(null);

  const closeView = useCallback(() => {
    setDetailsOpen(false);
  }, []);

  const openView = useCallback(
    async (t: Team) => {
      if (viewLoadingId === t.id) return;

      setViewLoadingId(t.id);
      try {
        const full = await getTeam(t.id);
        setDetailsTeam(full);
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
    setSelectedTeam(null);
    setModalMode("create");
    setModalOpen(true);
  }, []);

  const closeModal = useCallback(() => {
    if (submitting) return;
    setModalOpen(false);
  }, [submitting]);

  const openEdit = useCallback(
    async (t: Team) => {
      if (editLoadingId === t.id) return;

      setEditLoadingId(t.id);
      try {
        const full = await getTeam(t.id);
        setSelectedTeam(full);
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

  const deleteTeam = useCallback(
    async (t: Team) => {
      const ok = await confirm({
        title: "Supprimer l’équipe",
        description: `Confirmer la suppression de "${t.name}" ?`,
        confirmText: "Supprimer",
        cancelText: "Annuler",
        variant: "danger",
      });
      if (!ok) return;

      try {
        await removeTeam(t.id);
        toast.success("Équipe supprimée", {
          description: `"${t.name}" a été supprimée.`,
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

  const submitForm = useCallback(
    async (values: TeamBase) => {
      setSubmitting(true);
      try {
        if (modalMode === "create") {
          await createTeam(values);
          toast.success("Équipe créée");
        } else {
          if (!selectedTeam) return;

          const patch = buildTeamPatch(selectedTeam, values);

          // Si rien n'a changé, on évite un PATCH inutile
          if (Object.keys(patch).length === 0) {
            toast.message("Aucun changement");
            setModalOpen(false);
            return;
          }

          await updateTeam(selectedTeam.id, patch);
          toast.success("Équipe mise à jour");
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
    [modalMode, refresh, selectedTeam]
  );

  return {
    // state
    detailsOpen,
    detailsTeam,
    viewLoadingId,

    modalOpen,
    modalMode,
    selectedTeam,
    submitting,
    editLoadingId,

    // actions
    openCreate,
    openEdit,
    closeModal,
    deleteTeam,
    submitForm,

    openView,
    closeView,
  };
}
