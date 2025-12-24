"use client";

import { useMemo, useRef } from "react";

import { useConfirm } from "@/components/admin/dialogs/useConfirm";
import { ListPage } from "@/components/admin/listing/ListPage";
import { getAgentColumns } from "@/features/agents/agents.columns";
import { listAgents, removeAgent } from "@/services/agents.service";
import type { Agent } from "@/types";

export default function AgentsPage() {
  const listingRef = useRef<{ refresh: () => void } | null>(null);
  const { confirm, ConfirmDialog } = useConfirm();

  const fetcher = useMemo(
    () => ({ page, pageSize }: { page: number; pageSize: number }) =>
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

      await removeAgent(a.id);
      listingRef.current?.refresh();
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
      />

      <ConfirmDialog />
    </>
  );
}
