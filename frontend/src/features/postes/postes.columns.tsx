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
    { key: "nom", header: "Nom", cell: (a) => <span className="font-medium">{a.nom}</span> },
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
