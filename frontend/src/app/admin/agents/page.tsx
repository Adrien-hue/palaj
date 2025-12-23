"use client";

import { ListPage } from "@/components/admin/listing/ListPage";
import type { Agent } from "@/types";
import type { ColumnDef } from "@/components/admin/listing/DataTable";

const columns: ColumnDef<Agent>[] = [
  { key: "nom", header: "Nom", cell: (a) => <span className="font-medium">{a.nom}</span> },
  { key: "prenom", header: "Prénom", cell: (a) => a.prenom },
  { key: "code", header: "Code", cell: (a) => <span className="text-zinc-600">{a.code_personnel}</span> },
  {
    key: "actif",
    header: "Actif",
    cell: (a) => (
      <span
        className={[
          "inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium",
          a.actif ? "bg-green-100 text-green-700" : "bg-zinc-100 text-zinc-600",
        ].join(" ")}
      >
        {a.actif ? "Actif" : "Inactif"}
      </span>
    ),
  },
  {
    key: "actions",
    header: "Actions",
    cell: (a) => (
      <div className="flex gap-2">
        <button className="rounded-lg px-2 py-1 text-sm hover:bg-zinc-100" onClick={() => alert(`TODO voir ${a.id}`)}>
          Voir
        </button>
        <button className="rounded-lg px-2 py-1 text-sm hover:bg-zinc-100" onClick={() => alert(`TODO edit ${a.id}`)}>
          Éditer
        </button>
        <button className="rounded-lg px-2 py-1 text-sm text-red-600 hover:bg-red-50" onClick={() => alert(`TODO delete ${a.id}`)}>
          Supprimer
        </button>
      </div>
    ),
  },
];

export default function AgentsPage() {
  return (
    <ListPage<Agent>
      title="Agents"
      description="Gestion des agents"
      path="/agents"
      columns={columns}
      getRowId={(a) => a.id}
      headerRight={
        <button
          className="rounded-xl bg-zinc-900 px-4 py-2 text-sm font-medium text-white hover:bg-zinc-800"
          onClick={() => alert("TODO ouvrir modal Create")}
        >
          Créer
        </button>
      }
      emptyTitle="Aucun agent"
      emptyDescription="Commence par créer ton premier agent."
    />
  );
}
