"use client";

import { useMemo, useRef } from "react";

import { useConfirm } from "@/components/admin/dialogs/useConfirm";
import { ListPage } from "@/components/admin/listing/ListPage";
import { useToast } from "@/components/admin/toast/ToastProvider";
import { Button, Dialog, SecondaryButton } from "@/components/ui";
import { getAgentColumns } from "@/features/agents/agents.columns";
import AgentDetails from "@/features/agents/agent.details";
import AgentForm from "@/features/agents/agent.form";
import { listAgents } from "@/services/agents.service";
import type { Agent } from "@/types";
import { useAgentsCrud } from "@/features/agents/useAgentCrud";

export default function AgentsPage() {
  const refreshRef = useRef<null | (() => void)>(null);
  const { confirm, ConfirmDialog } = useConfirm();
  const { showToast } = useToast();

  const crud = useAgentsCrud({
    confirm,
    showToast,
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
    [crud.deleteAgent, crud.openEdit, crud.toggleActive, crud.togglingIds]
  );

  return (
    <>
      <ListPage<Agent>
        title="Agents"
        description="Gestion des agents"
        fetcher={fetcher}
        columns={columns}
        getRowId={(a) => a.id}
        headerRight={
          <Button variant="success" onClick={crud.openCreate}>
            Créer
          </Button>
        }
        emptyTitle="Aucun agent"
        emptyDescription="Commence par créer ton premier agent."
        onReady={(api) => {
          refreshRef.current = api.refresh;
        }}
      />

      <ConfirmDialog />

      <Dialog
        open={crud.detailsOpen}
        title="Détail agent"
        onClose={crud.closeView}
        maxWidthClassName="max-w-2xl"
      >
        {crud.detailsAgent ? (
          <div className="space-y-4">
            <AgentDetails agent={crud.detailsAgent as any} />

            <div className="flex justify-end gap-2">
              <SecondaryButton onClick={crud.closeView}>Fermer</SecondaryButton>

              <Button
                onClick={() => {
                  crud.closeView();
                  crud.openEdit(crud.detailsAgent as any);
                }}
              >
                Éditer
              </Button>
            </div>
          </div>
        ) : (
          <div className="text-sm text-zinc-600">Aucune donnée.</div>
        )}
      </Dialog>

      <Dialog
        open={crud.modalOpen}
        title={
          crud.modalMode === "create" ? "Créer un agent" : "Modifier l'agent"
        }
        onClose={crud.closeModal}
      >
        <AgentForm
          key={`${crud.modalMode}-${crud.selectedAgent?.id ?? "new"}`}
          mode={crud.modalMode}
          initialAgent={crud.selectedAgent}
          submitting={crud.submitting}
          onCancel={crud.closeModal}
          onSubmit={crud.submitForm}
        />
      </Dialog>
    </>
  );
}
