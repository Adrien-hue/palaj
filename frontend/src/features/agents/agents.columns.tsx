"use client";

import type { ColumnDef } from "@/components/admin/listing/DataTable";
import RowActions from "@/components/admin/listing/RowActions";
import { ActiveSwitch } from "@/components/ui";
import type { Agent } from "@/types";

export function getAgentColumns(opts: {
  onView: (a: Agent) => void;
  onEdit: (a: Agent) => void;
  onDelete: (a: Agent) => void;
  onToggleActive: (a: Agent) => void;
  togglingIds?: Set<number>;
}): ColumnDef<Agent>[] {
  return [
    { key: "nom", header: "Nom", cell: (a) => <span className="font-medium">{a.nom}</span> },
    { key: "prenom", header: "Prénom", cell: (a) => a.prenom },
    { key: "code", header: "Code", cell: (a) => <span className="text-zinc-600">{a.code_personnel}</span> },
    {
      key: "actif",
      header: "Actif",
      cell: (a) => (
        <ActiveSwitch
          checked={a.actif}
          onToggle={() => opts.onToggleActive(a)}
          disabled={opts.togglingIds?.has(a.id)}
          tooltipOn="Désactiver l'agent"
          tooltipOff="Activer l'agent"
        />
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
