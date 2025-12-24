"use client";

import { useMemo, useRef, useState } from "react";

import { useConfirm } from "@/components/admin/dialogs/useConfirm";
import { ListPage } from "@/components/admin/listing/ListPage";
import { useToast } from "@/components/admin/toast/ToastProvider";
import { getAgentColumns } from "@/features/agents/agents.columns";
import { activateAgent, deactivateAgent, listAgents, removeAgent } from "@/services/agents.service";
import type { Agent } from "@/types";

export default function AgentsPage() {
  const refreshRef = useRef<null | (() => void)>(null);
  const { confirm, ConfirmDialog } = useConfirm();
  const { showToast } = useToast();
  const [togglingIds, setTogglingIds] = useState<Set<number>>(new Set());

  const fetcher = useMemo(
    () =>
      ({ page, pageSize }: { page: number; pageSize: number }) =>
        listAgents({ page, page_size: pageSize }),
    []
  );

  const columns = getAgentColumns({
    onView: (a) => alert(`TODO voir ${a.id}`),
    onEdit: (a) => alert(`TODO edit ${a.id}`),
    onDelete: async (a) => {
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

        refreshRef.current?.();
      } catch (e) {
        showToast({
          type: "error",
          title: "Suppression impossible",
          message: e instanceof Error ? e.message : "Erreur inconnue",
          durationMs: 6000,
        });
      }
    },
    togglingIds,
    onToggleActive: async (a) => {
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
          message: `${a.nom} ${a.prenom} est maintenant ${
            a.actif ? "inactif" : "actif"
          }.`,
        });

        refreshRef.current?.();
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
  });

  return (
    <>
      <ListPage<Agent>
        title="Agents"
        description="Gestion des agents"
        fetcher={fetcher}
        columns={columns}
        getRowId={(a) => a.id}
        headerRight={
          <button
            className="rounded-xl bg-zinc-900 px-4 py-2 text-sm font-medium text-white hover:bg-zinc-800"
            onClick={() => alert("TODO ouvrir modal Create")}
          >
            Créer
          </button>
        }
        emptyTitle="Aucun agent"
        emptyDescription="Commence par créer ton premier agent."
        onReady={(api) => {
          refreshRef.current = api.refresh;
        }}
      />

      <ConfirmDialog />
    </>
  );
}
