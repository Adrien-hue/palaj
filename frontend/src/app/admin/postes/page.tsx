"use client";

import { useMemo, useRef } from "react";

import { useConfirm } from "@/components/admin/dialogs/useConfirm";
import { ListPage } from "@/components/admin/listing/ListPage";
import { useToast } from "@/components/admin/toast/ToastProvider";
import { Button, Dialog, SecondaryButton } from "@/components/ui";

import { getPosteColumns } from "@/features/postes/postes.columns";
import PosteForm from "@/features/postes/poste.form";
import { usePosteCrud } from "@/features/postes/usePosteCrud";

import { listPostes } from "@/services";
import type { Poste } from "@/types";
import PosteDetails from "@/features/postes/poste.details";

export default function PostesPage() {
  const refreshRef = useRef<null | (() => void)>(null);
  const { confirm, ConfirmDialog } = useConfirm();
  const { showToast } = useToast();

  const crud = usePosteCrud({
    confirm,
    showToast,
    refresh: () => refreshRef.current?.(),
  });

  const fetcher = useMemo(
    () => ({ page, pageSize }: { page: number; pageSize: number }) =>
      listPostes({ page, page_size: pageSize }),
    []
  );

  const columns = useMemo(
    () =>
      getPosteColumns({
        onView: crud.openView,
        onEdit: crud.openEdit,
        onDelete: crud.deletePoste,
      }),
    [crud.openView, crud.deletePoste, crud.openEdit]
  );

  return (
    <>
      <ListPage<Poste>
        title="Postes"
        description="Gestion des postes"
        fetcher={fetcher}
        columns={columns}
        getRowId={(p) => p.id}
        headerRight={
          <Button variant="success" onClick={crud.openCreate}>
            Créer
          </Button>
        }
        emptyTitle="Aucun poste"
        emptyDescription="Commence par créer ton premier poste."
        onReady={(api) => {
          refreshRef.current = api.refresh;
        }}
      />

      <ConfirmDialog />

      <Dialog open={crud.detailsOpen} title="Détail poste" onClose={crud.closeView} maxWidthClassName="max-w-2xl">
        {crud.detailsPoste ? (
          <div className="space-y-4">
            <PosteDetails poste={crud.detailsPoste} />

            <div className="flex justify-end gap-2">
              <SecondaryButton type="button" onClick={crud.closeView}>
                Fermer
              </SecondaryButton>

              <Button
                type="button"
                onClick={() => {
                  crud.closeView();
                  crud.openEdit(crud.detailsPoste!);
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
        title={crud.modalMode === "create" ? "Créer un poste" : "Modifier le poste"}
        onClose={crud.closeModal}
      >
        <PosteForm
          key={`${crud.modalMode}-${crud.selectedPoste?.id ?? "new"}`}
          mode={crud.modalMode}
          initialPoste={crud.selectedPoste}
          submitting={crud.submitting}
          onCancel={crud.closeModal}
          onSubmit={crud.submitForm}
        />
      </Dialog>
    </>
  );
}
