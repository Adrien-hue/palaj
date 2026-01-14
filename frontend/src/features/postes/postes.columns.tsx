"use client";

import type { ColumnDef } from "@/components/admin/listing/DataTable";
import RowActions from "@/components/admin/listing/RowActions";
import type { Poste } from "@/types";

export function getPosteColumns(opts: {
  onView: (p: Poste) => void;
  onEdit: (p: Poste) => void;
  onDelete: (p: Poste) => void;
}): ColumnDef<Poste>[] {
  return [
    { key: "nom", header: "Nom", cell: (p) => <span className="font-medium">{p.nom}</span> },
    {
      key: "actions",
      header: "",
      headerClassName: "w-[96px]",
      className: "text-right",
      cell: (p) => (
        <RowActions
          onView={() => opts.onView(p)}
          onEdit={() => opts.onEdit(p)}
          onDelete={() => opts.onDelete(p)}
        />
      ),
    },
  ];
}
