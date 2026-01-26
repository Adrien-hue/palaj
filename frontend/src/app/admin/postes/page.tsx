"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { toast } from "sonner";

import type { Poste } from "@/types";
import { listPostes } from "@/services";

import { useConfirm } from "@/hooks/useConfirm";
import { usePosteCrud } from "@/features/postes/usePosteCrud";

import { ClientDataTable } from "@/components/tables/ClientDataTable";
import { getPosteTableColumns } from "@/features/postes/postes.table-columns";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";

import PosteDetails from "@/features/postes/poste.details";
import PosteForm, { type PosteFormHandle } from "@/features/postes/poste.form";

async function fetchAllPostes() {
  const pageSize = 200;
  let page = 1;
  const all: Poste[] = [];

  while (true) {
    const res = await listPostes({ page, page_size: pageSize });
    all.push(...res.items);
    if (res.items.length < pageSize) break;
    page += 1;
  }

  return all;
}

export default function PostesPage() {
  const { confirm, ConfirmDialog } = useConfirm();

  const [postes, setPostes] = useState<Poste[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refreshRef = useRef<null | (() => void)>(null);
  const refresh = useCallback(() => refreshRef.current?.(), []);

  const crud = usePosteCrud({
    confirm,
    refresh,
    showToast: ({ type, title, message }) => {
      if (type === "success") toast.success(title, { description: message });
      else if (type === "error") toast.error(title, { description: message });
      else toast(title, { description: message });
    },
  });

  const formRef = useRef<PosteFormHandle | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function run() {
      setLoading(true);
      setError(null);
      try {
        const all = await fetchAllPostes();
        if (!cancelled) setPostes(all);
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : "Erreur inconnue");
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
      getPosteTableColumns({
        onView: crud.openView,
        onEdit: crud.openEdit,
        onDelete: crud.deletePoste,
      }),
    [crud]
  );

  const handleEditFromDetails = useCallback(() => {
    if (!crud.detailsPoste) return;
    const poste = crud.detailsPoste as any;
    crud.closeView();
    crud.openEdit(poste);
  }, [crud]);

  return (
    <>
      {/* Header */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0">
          <h1 className="truncate text-2xl font-semibold tracking-tight">Postes</h1>
          <p className="mt-1 text-sm text-muted-foreground">Gestion des postes</p>
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
              <CardDescription className="text-destructive">{error}</CardDescription>
            </CardHeader>
            <CardContent>
              <Button onClick={refresh}>Réessayer</Button>
            </CardContent>
          </Card>
        ) : postes.length === 0 ? (
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Aucun poste</CardTitle>
              <CardDescription>Commence par créer ton premier poste.</CardDescription>
            </CardHeader>
            <CardContent>
              <Button onClick={crud.openCreate}>Créer un poste</Button>
            </CardContent>
          </Card>
        ) : (
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-base">Liste des postes</CardTitle>
              <CardDescription>Recherche, tri, pagination et colonnes configurables.</CardDescription>
            </CardHeader>

            <CardContent className="p-0">
              <div className="p-4 pt-0">
                <ClientDataTable<Poste>
                  data={postes}
                  columns={columns}
                  searchPlaceholder="Rechercher un poste…"
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
      <Dialog open={crud.detailsOpen} onOpenChange={(v) => !v && crud.closeView()}>
        <DialogContent className="sm:max-w-3xl p-0">
          <DialogHeader className="px-6 pt-6">
            <DialogTitle>Détail poste</DialogTitle>
          </DialogHeader>

          <div className="px-6 py-4 max-h-[70dvh] overflow-auto">
            {crud.detailsPoste ? (
              <PosteDetails poste={crud.detailsPoste as any} confirm={confirm} />
            ) : (
              <div className="text-sm text-muted-foreground">Aucune donnée.</div>
            )}
          </div>

          <div className="flex items-center justify-end gap-2 border-t bg-background px-6 py-4">
            <Button variant="outline" type="button" onClick={crud.closeView}>
              Fermer
            </Button>
            <Button type="button" onClick={handleEditFromDetails} disabled={!crud.detailsPoste}>
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
              {crud.modalMode === "create" ? "Créer un poste" : "Modifier le poste"}
            </DialogTitle>
          </DialogHeader>

          <div className="px-6 py-4 max-h-[70dvh] overflow-auto">
            <PosteForm
              ref={formRef}
              mode={crud.modalMode}
              initialPoste={crud.selectedPoste}
              submitting={crud.submitting}
              onSubmit={crud.submitForm}
            />
          </div>

          <div className="flex items-center justify-end gap-2 border-t bg-background px-6 py-4">
            <Button type="button" variant="outline" onClick={crud.closeModal} disabled={crud.submitting}>
              Annuler
            </Button>
            <Button type="button" onClick={() => formRef.current?.submit()} disabled={crud.submitting}>
              {crud.modalMode === "create" ? "Créer" : "Enregistrer"}
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
}
