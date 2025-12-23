"use client";

import { ListPage } from "@/components/admin/listing/ListPage";
import type { Poste } from "@/types";
import type { ColumnDef } from "@/components/admin/listing/DataTable";

const columns: ColumnDef<Poste>[] = [
  { key: "nom", header: "Nom", cell: (p) => <span className="font-medium">{p.nom}</span> },
  {
    key: "actions",
    header: "Actions",
    cell: (p) => (
      <div className="flex gap-2">
        <button className="rounded-lg px-2 py-1 text-sm hover:bg-zinc-100" onClick={() => alert(`TODO voir ${p.id}`)}>
          Voir
        </button>
        <button className="rounded-lg px-2 py-1 text-sm hover:bg-zinc-100" onClick={() => alert(`TODO edit ${p.id}`)}>
          Éditer
        </button>
        <button className="rounded-lg px-2 py-1 text-sm text-red-600 hover:bg-red-50" onClick={() => alert(`TODO delete ${p.id}`)}>
          Supprimer
        </button>
      </div>
    ),
  },
];

export default function PostesPage() {
  return (
    <ListPage<Poste>
      title="Postes"
      description="Gestion des postes"
      path="/postes"
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
  );
}
