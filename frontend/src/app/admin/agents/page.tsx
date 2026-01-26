"use client";

import { useEffect, useMemo, useRef, useState, useCallback } from "react";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

import type { Agent } from "@/types";
import { listAgents } from "@/services/agents.service";

import { useConfirm } from "@/hooks/useConfirm";
import { useAgentsCrud } from "@/features/agents/useAgentCrud";
import AgentDetails from "@/features/agents/agent.details";
import AgentForm, { type AgentFormHandle } from "@/features/agents/agent.form";

import { ClientDataTable } from "@/components/tables/ClientDataTable";
import { getAgentTableColumns } from "@/features/agents/agents.table-columns";

async function fetchAllAgents() {
  const pageSize = 200;
  let page = 1;
  const all: Agent[] = [];

  while (true) {
    const res = await listAgents({ page, page_size: pageSize });
    all.push(...res.items);
    if (res.items.length < pageSize) break;
    page += 1;
  }

  return all;
}

export default function AgentsPage() {
  const { confirm, ConfirmDialog } = useConfirm();

  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refreshRef = useRef<null | (() => void)>(null);
  const refresh = useCallback(() => refreshRef.current?.(), []);

  const crud = useAgentsCrud({ confirm, refresh });

  const formRef = useRef<AgentFormHandle | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function run() {
      setLoading(true);
      setError(null);
      try {
        const all = await fetchAllAgents();
        if (!cancelled) setAgents(all);
      } catch (e) {
        if (!cancelled)
          setError(e instanceof Error ? e.message : "Erreur inconnue");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    refreshRef.current = run;
    run();

    return () => {
      cancelled = true;
    };
  }, []);

  const columns = useMemo(
    () =>
      getAgentTableColumns({
        onView: crud.openView,
        onEdit: crud.openEdit,
        onDelete: crud.deleteAgent,
        onToggleActive: crud.toggleActive,
        togglingIds: crud.togglingIds,
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
        <AgentDetails agent={crud.detailsAgent as any} confirm={confirm} />
      ) : (
        <div className="text-sm text-muted-foreground">Aucune donnée.</div>
      ),
    [crud.detailsAgent]
  );

  return (
    <>
      {/* Page header */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0">
          <h1 className="truncate text-2xl font-semibold tracking-tight">
            Agents
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Gestion des agents
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button variant="outline" onClick={refresh} disabled={loading}>
            Actualiser
          </Button>
          <Button onClick={crud.openCreate}>Créer</Button>
        </div>
      </div>

      {/* Content */}
      <div className="mt-4">
        {loading ? (
          <Card>
            <CardHeader className="space-y-2">
              <Skeleton className="h-5 w-40" />
              <Skeleton className="h-4 w-72" />
            </CardHeader>
            <CardContent className="space-y-3">
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
            </CardContent>
          </Card>
        ) : error ? (
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Erreur</CardTitle>
              <CardDescription className="text-destructive">
                {error}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Button onClick={refresh}>Réessayer</Button>
            </CardContent>
          </Card>
        ) : agents.length === 0 ? (
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Aucun agent</CardTitle>
              <CardDescription>
                Commence par créer ton premier agent.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Button onClick={crud.openCreate}>Créer un agent</Button>
            </CardContent>
          </Card>
        ) : (
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-base">Liste des agents</CardTitle>
              <CardDescription>
                Recherche, tri, pagination et colonnes configurables.
              </CardDescription>
            </CardHeader>

            <CardContent className="p-0">
              <div className="p-4 pt-0">
                <ClientDataTable<Agent>
                  data={agents}
                  columns={columns}
                  searchPlaceholder="Rechercher un agent…"
                  initialPageSize={20}
                  maxHeightClassName="max-h-[calc(100dvh-360px)]"
                  enableColumnVisibility={false}
                />
              </div>
            </CardContent>
          </Card>
        )}
      </div>

      <ConfirmDialog />

      {/* Details */}
      <Dialog
        open={crud.detailsOpen}
        onOpenChange={(v) => !v && crud.closeView()}
      >
        <DialogContent className="sm:max-w-2xl p-0">
          <DialogHeader className="px-6 pt-6">
            <DialogTitle>Détail agent</DialogTitle>
          </DialogHeader>

          <div className="px-6 py-4 max-h-[70dvh] overflow-auto">
            {crud.detailsAgent ? (
              <AgentDetails
                agent={crud.detailsAgent as any}
                confirm={confirm}
              />
            ) : (
              <div className="text-sm text-muted-foreground">
                Aucune donnée.
              </div>
            )}
          </div>

          <div className="flex items-center justify-end gap-2 border-t bg-background px-6 py-4">
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
      <Dialog
        open={crud.modalOpen}
        onOpenChange={(v) => {
          if (!v && !crud.submitting) crud.closeModal();
        }}
      >
        <DialogContent
          className="sm:max-w-xl p-0"
          onPointerDownOutside={(e) => crud.submitting && e.preventDefault()}
          onEscapeKeyDown={(e) => crud.submitting && e.preventDefault()}
        >
          <DialogHeader className="px-6 pt-6">
            <DialogTitle>
              {crud.modalMode === "create"
                ? "Créer un agent"
                : "Modifier l'agent"}
            </DialogTitle>
          </DialogHeader>

          <div className="px-6 py-4 max-h-[70dvh] overflow-auto">
            <AgentForm
              ref={formRef}
              mode={crud.modalMode}
              initialAgent={crud.selectedAgent}
              submitting={crud.submitting}
              onSubmit={crud.submitForm}
            />
          </div>

          <div className="flex items-center justify-end gap-2 border-t bg-background px-6 py-4">
            <Button
              type="button"
              variant="outline"
              onClick={crud.closeModal}
              disabled={crud.submitting}
            >
              Annuler
            </Button>

            <Button
              type="button"
              onClick={() => formRef.current?.submit()}
              disabled={crud.submitting}
            >
              {crud.modalMode === "create" ? "Créer" : "Enregistrer"}
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
}
