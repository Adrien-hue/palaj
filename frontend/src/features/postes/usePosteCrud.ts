"use client";

import { useCallback, useState } from "react";
import type { Poste, PosteDetail, PatchPosteBody } from "@/types";

import {
  createPoste,
  getPoste,
  patchPoste,
  removePoste,
} from "@/services/postes.service";

import { buildPostePatch } from "@/features/postes/buildPostePatch";
import type { ConfirmOptions } from "@/hooks/useConfirm";

export type ShowToastFn = (t: {
  type: "success" | "error" | "info";
  title: string;
  message?: string;
  durationMs?: number;
}) => void;

export function usePosteCrud(opts: {
  confirm: (opts: ConfirmOptions) => Promise<boolean>;
  refresh: () => void;
  showToast?: ShowToastFn;
}) {
  const { confirm, refresh, showToast } = opts;

  const [detailsOpen, setDetailsOpen] = useState(false);
  const [detailsPoste, setDetailsPoste] = useState<PosteDetail | null>(null);
  const [viewLoadingId, setViewLoadingId] = useState<number | null>(null);

  const [modalOpen, setModalOpen] = useState(false);
  const [modalMode, setModalMode] = useState<"create" | "edit">("create");
  const [selectedPoste, setSelectedPoste] = useState<PosteDetail | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const [editLoadingId, setEditLoadingId] = useState<number | null>(null);

  const closeView = useCallback(() => {
    setDetailsOpen(false);
  }, []);

  const openView = useCallback(
    async (p: Poste) => {
      if (viewLoadingId === p.id) return;

      setViewLoadingId(p.id);
      try {
        const full = await getPoste(p.id);
        setDetailsPoste(full);
        setDetailsOpen(true);
      } catch (e) {
        showToast?.({
          type: "error",
          title: "Chargement impossible",
          message: e instanceof Error ? e.message : "Erreur inconnue",
          durationMs: 6000,
        });
      } finally {
        setViewLoadingId(null);
      }
    },
    [showToast, viewLoadingId]
  );

  const openCreate = useCallback(() => {
    setSelectedPoste(null);
    setModalMode("create");
    setModalOpen(true);
  }, []);

  const closeModal = useCallback(() => {
    if (submitting) return;
    setModalOpen(false);
  }, [submitting]);

  const openEdit = useCallback(
    async (p: Poste) => {
      if (editLoadingId === p.id) return;

      setEditLoadingId(p.id);
      try {
        const full = await getPoste(p.id);
        setSelectedPoste(full);
        setModalMode("edit");
        setModalOpen(true);
      } catch (e) {
        showToast?.({
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

  const deletePoste = useCallback(
    async (p: Poste) => {
      const ok = await confirm({
        title: "Supprimer le poste",
        description: `Confirmer la suppression de "${p.nom}" ?`,
        confirmText: "Supprimer",
        cancelText: "Annuler",
        variant: "danger",
      });
      if (!ok) return;

      try {
        await removePoste(p.id);
        showToast?.({
          type: "success",
          title: "Poste supprimé",
          message: `"${p.nom}" a été supprimé.`,
        });
        refresh();
      } catch (e) {
        showToast?.({
          type: "error",
          title: "Suppression impossible",
          message: e instanceof Error ? e.message : "Erreur inconnue",
          durationMs: 6000,
        });
      }
    },
    [confirm, refresh, showToast]
  );

  const submitForm = useCallback(
    async (values: { nom: string }) => {
      setSubmitting(true);
      try {
        const nom = values.nom.trim();

        if (modalMode === "create") {
          await createPoste({ nom });
          showToast?.({ type: "success", title: "Poste créé" });
        } else {
          if (!selectedPoste) return;

          const patch: PatchPosteBody = buildPostePatch(selectedPoste, { nom });
          await patchPoste(selectedPoste.id, patch);

          showToast?.({ type: "success", title: "Poste mis à jour" });
        }

        setModalOpen(false);
        refresh();
      } catch (e) {
        showToast?.({
          type: "error",
          title: "Enregistrement impossible",
          message: e instanceof Error ? e.message : "Erreur inconnue",
          durationMs: 6000,
        });
      } finally {
        setSubmitting(false);
      }
    },
    [modalMode, refresh, selectedPoste, showToast]
  );

  return {
    // state
    modalOpen,
    modalMode,
    selectedPoste,
    submitting,
    editLoadingId,
    detailsOpen,
    detailsPoste,
    viewLoadingId,

    // actions
    openCreate,
    openEdit,
    closeModal,
    deletePoste,
    submitForm,
    openView,
    closeView,
  };
}
