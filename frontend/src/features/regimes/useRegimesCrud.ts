"use client";

import { useCallback, useState } from "react";
import { toast } from "sonner";

import type { Regime, RegimeDetail, RegimeBase } from "@/types";
import { createRegime, getRegime, updateRegime, removeRegime } from "@/services/regimes.service";
import { buildRegimePatch } from "@/features/regimes/buildRegimePatch";

import type { ConfirmOptions } from "@/hooks/useConfirm";

export type ConfirmFn = (opts: ConfirmOptions) => Promise<boolean>;

export function useRegimeCrud(opts: {
  confirm: ConfirmFn;
  refresh: () => void;
}) {
  const { confirm, refresh } = opts;

  const [detailsOpen, setDetailsOpen] = useState(false);
  const [detailsRegime, setDetailsRegime] = useState<RegimeDetail | null>(null);
  const [viewLoadingId, setViewLoadingId] = useState<number | null>(null);

  const [modalOpen, setModalOpen] = useState(false);
  const [modalMode, setModalMode] = useState<"create" | "edit">("create");
  const [selectedRegime, setSelectedRegime] = useState<RegimeDetail | null>(null);
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
        toast.error("Chargement impossible", {
          description: e instanceof Error ? e.message : "Erreur inconnue",
        });
      } finally {
        setEditLoadingId(null);
      }
    },
    [editLoadingId]
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
        toast.success("Régime supprimé", { description: `"${r.nom}" a été supprimé.` });
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
    async (values: RegimeBase) => {
      setSubmitting(true);
      try {
        if (modalMode === "create") {
          await createRegime(values);
          toast.success("Régime créé");
        } else {
          if (!selectedRegime) return;

          const patch = buildRegimePatch(selectedRegime, values);
          await updateRegime(selectedRegime.id, patch);
          toast.success("Régime mis à jour");
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
    [modalMode, refresh, selectedRegime]
  );

  return {
    // state
    detailsOpen,
    detailsRegime,
    viewLoadingId,

    modalOpen,
    modalMode,
    selectedRegime,
    submitting,
    editLoadingId,

    // actions
    openCreate,
    openEdit,
    closeModal,
    deleteRegime,
    submitForm,

    openView,
    closeView,
  };
}
