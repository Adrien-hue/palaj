"use client";

import type { ColumnDef } from "@/components/admin/listing/DataTable";
import RowActions from "@/components/admin/listing/RowActions";
import type { Regime } from "@/types";

export function getRegimeColumns(opts: {
  onView: (r: Regime) => void;
  onEdit: (r: Regime) => void;
  onDelete: (r: Regime) => void;
}): ColumnDef<Regime>[] {
  return [
    { key: "nom", header: "Nom", cell: (r) => <span className="font-medium">{r.nom}</span> },
    { key: "desc", header: "Description", cell: (r) => <span className="font-medium">{r.desc}</span> },
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
