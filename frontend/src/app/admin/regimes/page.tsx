"use client";

import { useMemo, useRef } from "react";

import { useConfirm } from "@/components/admin/dialogs/useConfirm";
import { ListPage } from "@/components/admin/listing/ListPage";
import { getRegimeColumns } from "@/features/regimes/regimes.columns";
import { listRegimes, removeRegime } from "@/services";
import type { Regime } from "@/types";

export default function RegimesPage() {
  const listingRef = useRef<{ refresh: () => void } | null>(null);
  const { confirm, ConfirmDialog } = useConfirm();

  const fetcher = useMemo(
    () => ({ page, pageSize }: { page: number; pageSize: number }) =>
      listRegimes({ page, page_size: pageSize }),
    []
  );

  const columns = getRegimeColumns({
    onView: (r) => alert(`TODO voir ${r.id}`),
    onEdit: (r) => alert(`TODO edit ${r.id}`),
    onDelete: async (r) => {
      const ok = await confirm({
        title: "Supprimer le régime",
        description: `Confirmer la suppression du régime ${r.nom} ?`,
        confirmText: "Supprimer",
        cancelText: "Annuler",
        variant: "danger",
      });
      if (!ok) return;

      await removeRegime(r.id);
      listingRef.current?.refresh();
    },
  });

  return (
    <>
      <ListPage<Regime>
        title="Régimes"
        description="Gestion des régimes"
        fetcher={fetcher}
        columns={columns}
        getRowId={(r) => r.id}
        headerRight={
          <button
            className="rounded-xl bg-zinc-900 px-4 py-2 text-sm font-medium text-white hover:bg-zinc-800"
            onClick={() => alert("TODO ouvrir modal Create")}
          >
            Créer
          </button>
        }
        emptyTitle="Aucun régime"
        emptyDescription="Commence par créer ton premier régime."
      />
      
      <ConfirmDialog />
    </>
  );
}
