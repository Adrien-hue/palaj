"use client";

import type { ColumnDef } from "@/components/admin/listing/DataTable";
import RowActions from "@/components/admin/listing/RowActions";
import type { Agent } from "@/types";

export function getAgentColumns(opts: {
  onView: (a: Agent) => void;
  onEdit: (a: Agent) => void;
  onDelete: (a: Agent) => void;
}): ColumnDef<Agent>[] {
  return [
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
      header: "",
      headerClassName: "w-[96px]",
      className: "text-right",
      cell: (a) => (
        <RowActions
          onView={() => opts.onView(a)}
          onEdit={() => opts.onEdit(a)}
          onDelete={() => opts.onDelete(a)}
        />
      ),
    },
  ];
}
