"use client";

import { useMemo, useRef } from "react";

import { useConfirm } from "@/components/admin/dialogs/useConfirm";
import { ListPage } from "@/components/admin/listing/ListPage";
import { useToast } from "@/components/admin/toast/ToastProvider";
import { Button, Dialog, SecondaryButton } from "@/components/ui";

import { getRegimeColumns } from "@/features/regimes/regimes.columns";
import RegimeForm from "@/features/regimes/regime.form";
import RegimeDetails from "@/features/regimes/regime.details";
import { useRegimeCrud } from "@/features/regimes/useRegimesCrud";

import { listRegimes } from "@/services/regimes.service";
import type { Regime } from "@/types";

export default function RegimesPage() {
  const refreshRef = useRef<null | (() => void)>(null);
  const { confirm, ConfirmDialog } = useConfirm();
  const { showToast } = useToast();

  const crud = useRegimeCrud({
    confirm,
    showToast,
    refresh: () => refreshRef.current?.(),
  });

  const fetcher = useMemo(
    () =>
      ({ page, pageSize }: { page: number; pageSize: number }) =>
        listRegimes({ page, page_size: pageSize }),
    []
  );

  const columns = useMemo(
    () =>
      getRegimeColumns({
        onView: crud.openView,
        onEdit: crud.openEdit,
        onDelete: crud.deleteRegime,
      }),
    [crud.openView, crud.openEdit, crud.deleteRegime]
  );

  const detailsFooter = (
    <div className="flex justify-end gap-2">
      <SecondaryButton type="button" onClick={crud.closeView}>
        Fermer
      </SecondaryButton>

      <Button
        type="button"
        onClick={() => {
          crud.closeView();
          crud.openEdit(crud.detailsRegime as any);
        }}
        disabled={!crud.detailsRegime}
      >
        Éditer
      </Button>
    </div>
  );

  const detailsBody = crud.detailsRegime ? (
    <RegimeDetails regime={crud.detailsRegime as any} />
  ) : (
    <div className="text-sm text-zinc-600">Aucune donnée.</div>
  );

  return (
    <>
      <ListPage<Regime>
        title="Régimes"
        description="Gestion des régimes"
        fetcher={fetcher}
        columns={columns}
        getRowId={(r) => r.id}
        headerRight={
          <Button variant="success" onClick={crud.openCreate}>
            Créer
          </Button>
        }
        emptyTitle="Aucun régime"
        emptyDescription="Commence par créer ton premier régime."
        onReady={(api) => {
          refreshRef.current = api.refresh;
        }}
      />

      <ConfirmDialog />

      {/* Details */}
      <Dialog
        open={crud.detailsOpen}
        title="Détail régime"
        onClose={crud.closeView}
        maxWidthClassName="max-w-2xl"
        footer={detailsFooter}
      >
        {detailsBody}
      </Dialog>

      {/* Create/Edit */}
      <Dialog
        open={crud.modalOpen}
        title={crud.modalMode === "create" ? "Créer un régime" : "Modifier le régime"}
        onClose={crud.closeModal}
        maxWidthClassName="max-w-2xl"
      >
        <RegimeForm
          key={`${crud.modalMode}-${crud.selectedRegime?.id ?? "new"}`}
          mode={crud.modalMode}
          initialRegime={crud.selectedRegime}
          submitting={crud.submitting}
          onCancel={crud.closeModal}
          onSubmit={crud.submitForm}
        />
      </Dialog>
    </>
  );
}
