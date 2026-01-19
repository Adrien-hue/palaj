"use client";

import { useCallback, useState } from "react";
import type {
  Regime,
  RegimeDetail,
  RegimeBase,
} from "@/types";

import {
  createRegime,
  getRegime,
  updateRegime,
  removeRegime,
} from "@/services/regimes.service";

import { buildRegimePatch } from "@/features/regimes/buildRegimePatch";

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

export function useRegimeCrud(opts: {
  confirm: ConfirmFn;
  showToast: ShowToastFn;
  refresh: () => void;
}) {
  const { confirm, showToast, refresh } = opts;

  const [detailsOpen, setDetailsOpen] = useState(false);
  const [detailsRegime, setDetailsRegime] = useState<RegimeDetail | null>(null);
  const [viewLoadingId, setViewLoadingId] = useState<number | null>(null);

  const [modalOpen, setModalOpen] = useState(false);
  const [modalMode, setModalMode] = useState<"create" | "edit">("create");
  const [selectedRegime, setSelectedRegime] = useState<RegimeDetail | null>(
    null
  );
  const [submitting, setSubmitting] = useState(false);

  const [editLoadingId, setEditLoadingId] = useState<number | null>(null);

  const closeView = useCallback(() => {
    setDetailsOpen(false);
  }, []);

  const openView = useCallback(
    async (r: Regime) => {
      if (viewLoadingId === r.id) return;

      setViewLoadingId(r.id);
      try {
        const full = await getRegime(r.id);
        setDetailsRegime(full);
        setDetailsOpen(true);
      } catch (e) {
        showToast({
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
    setSelectedRegime(null);
    setModalMode("create");
    setModalOpen(true);
  }, []);

  const closeModal = useCallback(() => {
    if (submitting) return;
    setModalOpen(false);
  }, [submitting]);

  const openEdit = useCallback(
    async (r: Regime) => {
      if (editLoadingId === r.id) return;

      setEditLoadingId(r.id);
      try {
        const full = await getRegime(r.id);
        setSelectedRegime(full);
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

  const deleteRegime = useCallback(
    async (r: Regime) => {
      const ok = await confirm({
        title: "Supprimer le régime",
        description: `Confirmer la suppression de "${r.nom}" ?`,
        confirmText: "Supprimer",
        cancelText: "Annuler",
        variant: "danger",
      });
      if (!ok) return;

      try {
        await removeRegime(r.id);
        showToast({
          type: "success",
          title: "Régime supprimé",
          message: `"${r.nom}" a été supprimé.`,
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

  const submitForm = useCallback(
    async (values: RegimeBase) => {
      setSubmitting(true);
      try {
        if (modalMode === "create") {
          await createRegime(values); // values == CreateRegimeBody
          showToast({ type: "success", title: "Régime créé" });
        } else {
          if (!selectedRegime) return;
          const patch = buildRegimePatch(selectedRegime, values);
          await updateRegime(selectedRegime.id, patch);
          showToast({ type: "success", title: "Régime mis à jour" });
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
    [modalMode, refresh, selectedRegime, showToast]
  );

  return {
    // State
    modalOpen,
    modalMode,
    selectedRegime,
    submitting,
    editLoadingId,
    detailsOpen,
    detailsRegime,
    viewLoadingId,

    // Actions
    openCreate,
    openEdit,
    closeModal,
    deleteRegime,
    submitForm,
    openView,
    closeView,
  };
}
