"use client";

import { ListPage } from "@/components/admin/listing/ListPage";
import type { Regime } from "@/types";
import type { ColumnDef } from "@/components/admin/listing/DataTable";
  
const columns: ColumnDef<Regime>[] = [
  { key: "nom", header: "Nom", cell: (r) => <span className="font-medium">{r.nom}</span> },
  { key: "desc", header: "Description", cell: (r) => <span className="font-medium">{r.desc}</span> },
  {
    key: "actions",
    header: "Actions",
    cell: (r) => (
      <div className="flex gap-2">
        <button className="rounded-lg px-2 py-1 text-sm hover:bg-zinc-100" onClick={() => alert(`TODO voir ${r.id}`)}>
          Voir
        </button>
        <button className="rounded-lg px-2 py-1 text-sm hover:bg-zinc-100" onClick={() => alert(`TODO edit ${r.id}`)}>
          Éditer
        </button>
        <button className="rounded-lg px-2 py-1 text-sm text-red-600 hover:bg-red-50" onClick={() => alert(`TODO delete ${r.id}`)}>
          Supprimer
        </button>
      </div>
    ),
  },
];

export default function RegimesPage() {
  return (
    <ListPage<Regime>
      title="Régimes"
      description="Gestion des régimes"
      path="/regimes"
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
  );
}
