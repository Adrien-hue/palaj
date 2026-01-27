"use client";

import { useEffect, useMemo, useRef, useState, useCallback } from "react";

import { useConfirm } from "@/hooks/useConfirm";

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

import { ClientDataTable } from "@/components/tables/ClientDataTable";
import { getTeamColumns } from "@/features/teams/teams.table-columns";

import TeamForm, { type TeamFormHandle } from "@/features/teams/team.form";
import TeamDetails from "@/features/teams/team.details";
import { useTeamCrud } from "@/features/teams/useTeamsCrud";

import { listTeams } from "@/services/teams.service";
import type { Team } from "@/types";

async function fetchAllTeams() {
  const pageSize = 200;
  let page = 1;
  const all: Team[] = [];

  while (true) {
    const res = await listTeams({ page, page_size: pageSize });
    all.push(...res.items);
    if (res.items.length < pageSize) break;
    page += 1;
  }

  return all;
}

export default function TeamsPage() {
  const { confirm, ConfirmDialog } = useConfirm();

  const [teams, setTeams] = useState<Team[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refreshRef = useRef<null | (() => void)>(null);
  const refresh = useCallback(() => refreshRef.current?.(), []);

  const crud = useTeamCrud({ confirm, refresh: () => refreshRef.current?.() });

  const formRef = useRef<TeamFormHandle | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function run() {
      setLoading(true);
      setError(null);
      try {
        const all = await fetchAllTeams();

        // Tri par name (UX stable), même si la DataTable peut aussi trier
        all.sort((a, b) => a.name.localeCompare(b.name, "fr"));

        if (!cancelled) setTeams(all);
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
      getTeamColumns({
        onView: crud.openView,
        onEdit: crud.openEdit,
        onDelete: crud.deleteTeam,
      }),
    [crud]
  );

  const handleEditFromDetails = useCallback(() => {
    if (!crud.detailsTeam) return;
    const team = crud.detailsTeam as any;
    crud.closeView();
    crud.openEdit(team);
  }, [crud]);

  return (
    <>
      {/* Page header */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0">
          <h1 className="truncate text-2xl font-semibold tracking-tight">
            Équipes
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Gestion des équipes
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
        ) : teams.length === 0 ? (
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Aucune équipe</CardTitle>
              <CardDescription>
                Commence par créer ta première équipe.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Button onClick={crud.openCreate}>Créer une équipe</Button>
            </CardContent>
          </Card>
        ) : (
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-base">Liste des équipes</CardTitle>
              <CardDescription>
                Recherche, tri, pagination et colonnes configurables.
              </CardDescription>
            </CardHeader>

            <CardContent className="p-0">
              <div className="p-4 pt-0">
                <ClientDataTable<Team>
                  data={teams}
                  columns={columns}
                  searchPlaceholder="Rechercher une équipe…"
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
            <DialogTitle>Détail équipe</DialogTitle>
          </DialogHeader>

          <div className="px-6 py-4 max-h-[70dvh] overflow-auto">
            {crud.detailsTeam ? (
              <TeamDetails team={crud.detailsTeam as any} />
            ) : (
              <div className="text-sm text-muted-foreground">Aucune donnée.</div>
            )}
          </div>

          <div className="flex items-center justify-end gap-2 border-t bg-background px-6 py-4">
            <Button variant="outline" type="button" onClick={crud.closeView}>
              Fermer
            </Button>
            <Button
              type="button"
              onClick={handleEditFromDetails}
              disabled={!crud.detailsTeam}
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
                ? "Créer une équipe"
                : "Modifier l’équipe"}
            </DialogTitle>
          </DialogHeader>

          <div className="px-6 py-4 max-h-[70dvh] overflow-auto">
            <TeamForm
              ref={formRef}
              mode={crud.modalMode}
              initialTeam={crud.selectedTeam}
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
