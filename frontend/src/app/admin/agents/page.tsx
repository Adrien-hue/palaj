"use client";

import { useMemo, useRef, useCallback } from "react";

import { ListPage } from "@/components/admin/listing/ListPage";
import { Button } from "@/components/ui/button";

import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

import { useConfirm } from "@/hooks/useConfirm";
import { getAgentColumns } from "@/features/agents/agents.columns";
import AgentDetails from "@/features/agents/agent.details";
import AgentForm from "@/features/agents/agent.form";
import { listAgents } from "@/services/agents.service";
import type { Agent } from "@/types";
import { useAgentsCrud } from "@/features/agents/useAgentCrud";

export default function AgentsPage() {
  const refreshRef = useRef<null | (() => void)>(null);
  const { confirm, ConfirmDialog } = useConfirm();

  const crud = useAgentsCrud({
    confirm,
    refresh: () => refreshRef.current?.(),
  });

  const fetcher = useMemo(
    () =>
      ({ page, pageSize }: { page: number; pageSize: number }) =>
        listAgents({ page, page_size: pageSize }),
    []
  );

  const columns = useMemo(
    () =>
      getAgentColumns({
        onView: crud.openView,
        onEdit: crud.openEdit,
        onDelete: crud.deleteAgent,
        togglingIds: crud.togglingIds,
        onToggleActive: crud.toggleActive,
      }),
    [crud]
  );

  const handleEditFromDetails = useCallback(() => {
    if (!crud.detailsAgent) return;
    const agent = crud.detailsAgent as any;
    crud.closeView();
    crud.openEdit(agent);
  }, [crud]);

  const detailsBody = useMemo(
    () =>
      crud.detailsAgent ? (
        <AgentDetails agent={crud.detailsAgent as any} />
      ) : (
        <div className="text-sm text-muted-foreground">Aucune donnée.</div>
      ),
    [crud.detailsAgent]
  );

  return (
    <>
      <ListPage<Agent>
        title="Agents"
        description="Gestion des agents"
        fetcher={fetcher}
        columns={columns}
        getRowId={(a) => a.id}
        headerRight={<Button onClick={crud.openCreate}>Créer</Button>}
        emptyTitle="Aucun agent"
        emptyDescription="Commence par créer ton premier agent."
        onReady={(api) => {
          refreshRef.current = api.refresh;
        }}
      />

      <ConfirmDialog />

      {/* Details */}
      <Dialog open={crud.detailsOpen} onOpenChange={(v) => !v && crud.closeView()}>
        <DialogContent className="sm:max-w-2xl">
          <DialogHeader>
            <DialogTitle>Détail agent</DialogTitle>
          </DialogHeader>

          {detailsBody}

          <div className="mt-4 flex justify-end gap-2">
            <Button variant="outline" type="button" onClick={crud.closeView}>
              Fermer
            </Button>
            <Button
              type="button"
              onClick={handleEditFromDetails}
              disabled={!crud.detailsAgent}
            >
              Éditer
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Create / Edit */}
      <Dialog open={crud.modalOpen} onOpenChange={(v) => !v && crud.closeModal()}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              {crud.modalMode === "create" ? "Créer un agent" : "Modifier l'agent"}
            </DialogTitle>
          </DialogHeader>

          <AgentForm
            key={`${crud.modalMode}-${crud.selectedAgent?.id ?? "new"}`}
            mode={crud.modalMode}
            initialAgent={crud.selectedAgent}
            submitting={crud.submitting}
            onCancel={crud.closeModal}
            onSubmit={crud.submitForm}
          />
        </DialogContent>
      </Dialog>
    </>
  );
}
