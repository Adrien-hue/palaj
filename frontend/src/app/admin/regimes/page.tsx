"use client";

import { useEffect, useMemo, useRef, useState, useCallback } from "react";
import { toast } from "sonner";

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
import { getRegimeColumns } from "@/features/regimes/regimes.table-columns";

import RegimeForm, { type RegimeFormHandle } from "@/features/regimes/regime.form";
import RegimeDetails from "@/features/regimes/regime.details";
import { useRegimeCrud } from "@/features/regimes/useRegimesCrud";

import { listRegimes } from "@/services/regimes.service";
import type { Regime } from "@/types";

async function fetchAllRegimes() {
  const pageSize = 200;
  let page = 1;
  const all: Regime[] = [];

  while (true) {
    const res = await listRegimes({ page, page_size: pageSize });
    all.push(...res.items);
    if (res.items.length < pageSize) break;
    page += 1;
  }

  return all;
}

export default function RegimesPage() {
  const { confirm, ConfirmDialog } = useConfirm();

  const [regimes, setRegimes] = useState<Regime[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refreshRef = useRef<null | (() => void)>(null);
  const refresh = useCallback(() => refreshRef.current?.(), []);

  const crud = useRegimeCrud({ confirm, refresh: () => refreshRef.current?.() });

  const formRef = useRef<RegimeFormHandle | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function run() {
      setLoading(true);
      setError(null);
      try {
        const all = await fetchAllRegimes();
        if (!cancelled) setRegimes(all);
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
      getRegimeColumns({
        onView: crud.openView,
        onEdit: crud.openEdit,
        onDelete: crud.deleteRegime,
      }),
    [crud]
  );

  const handleEditFromDetails = useCallback(() => {
    if (!crud.detailsRegime) return;
    const regime = crud.detailsRegime as any;
    crud.closeView();
    crud.openEdit(regime);
  }, [crud]);

  return (
    <>
      {/* Page header */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0">
          <h1 className="truncate text-2xl font-semibold tracking-tight">
            Régimes
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Gestion des régimes
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
        ) : regimes.length === 0 ? (
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Aucun régime</CardTitle>
              <CardDescription>
                Commence par créer ton premier régime.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Button onClick={crud.openCreate}>Créer un régime</Button>
            </CardContent>
          </Card>
        ) : (
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-base">Liste des régimes</CardTitle>
              <CardDescription>
                Recherche, tri, pagination et colonnes configurables.
              </CardDescription>
            </CardHeader>

            <CardContent className="p-0">
              <div className="p-4 pt-0">
                <ClientDataTable<Regime>
                  data={regimes}
                  columns={columns}
                  searchPlaceholder="Rechercher un régime…"
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
            <DialogTitle>Détail régime</DialogTitle>
          </DialogHeader>

          <div className="px-6 py-4 max-h-[70dvh] overflow-auto">
            {crud.detailsRegime ? (
              <RegimeDetails regime={crud.detailsRegime as any} />
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
              disabled={!crud.detailsRegime}
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
                ? "Créer un régime"
                : "Modifier le régime"}
            </DialogTitle>
          </DialogHeader>

          <div className="px-6 py-4 max-h-[70dvh] overflow-auto">
            <RegimeForm
              ref={formRef}
              mode={crud.modalMode}
              initialRegime={crud.selectedRegime}
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
