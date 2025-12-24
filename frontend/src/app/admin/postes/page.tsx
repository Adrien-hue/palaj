"use client";

import { useMemo, useRef } from "react";

import { useConfirm } from "@/components/admin/dialogs/useConfirm";
import { ListPage } from "@/components/admin/listing/ListPage";
import { getPosteColumns } from "@/features/postes/postes.columns";
import { listPostes, removePoste } from "@/services";
import type { Poste } from "@/types";

export default function PostesPage() {
  const listingRef = useRef<{ refresh: () => void } | null>(null);
  const { confirm, ConfirmDialog } = useConfirm();

  const fetcher = useMemo(
    () => ({ page, pageSize }: { page: number; pageSize: number }) =>
      listPostes({ page, page_size: pageSize }),
    []
  );

  const columns = getPosteColumns({
      onView: (p) => alert(`TODO voir ${p.id}`),
      onEdit: (p) => alert(`TODO edit ${p.id}`),
      onDelete: async (p) => {
        const ok = await confirm({
          title: "Supprimer le poste",
          description: `Confirmer la suppression du poste ${p.nom} ?`,
          confirmText: "Supprimer",
          cancelText: "Annuler",
          variant: "danger",
        });
        if (!ok) return;
  
        await removePoste(p.id);
        listingRef.current?.refresh();
      },
    });

  return (
    <>
      <ListPage<Poste>
        title="Postes"
        description="Gestion des postes"
        fetcher={fetcher}
        columns={columns}
        getRowId={(p) => p.id}
        headerRight={
          <button
            className="rounded-xl bg-zinc-900 px-4 py-2 text-sm font-medium text-white hover:bg-zinc-800"
            onClick={() => alert("TODO ouvrir modal Create")}
          >
            Créer
          </button>
        }
        emptyTitle="Aucun poste"
        emptyDescription="Commence par créer ton premier poste."
      />
      
      <ConfirmDialog />
    </>
  );
}
