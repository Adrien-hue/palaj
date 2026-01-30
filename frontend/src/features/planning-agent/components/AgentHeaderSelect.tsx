"use client";

import * as React from "react";

import { EntityCombobox, type EntityComboboxItem } from "@/components/ui/entity-combobox";

type AgentListItem = {
  id: number;
  nom: string;
  prenom: string;
  code_personnel?: string | null;
  actif: boolean;
};

export function AgentHeaderSelect({
  agents,
  valueId,
  disabled,
  widthClassName = "w-[320px] sm:w-[380px]",
  onChange,
}: {
  agents: AgentListItem[];
  valueId: number | null;
  disabled?: boolean;
  widthClassName?: string;
  onChange?: (id: number | null) => void;
}) {

  const items: EntityComboboxItem[] = React.useMemo(() => {
    return agents
      .filter((a) => a.actif)
      .map((a) => ({
        id: a.id,
        label: `${a.prenom} ${a.nom}`,
        description: a.code_personnel ? `Matricule: ${a.code_personnel}` : undefined,
        keywords: `${a.prenom} ${a.nom} ${a.code_personnel ?? ""}`,
      }));
  }, [agents]);

  return (
    <EntityCombobox
      items={items}
      value={valueId}
      onChange={(id) => {
        const nextId = Number(id);
        if (onChange) {
          onChange(nextId);
          return;
        }
      }}
      placeholder="Choisir un agent…"
      searchPlaceholder="Rechercher un agent…"
      emptyText="Aucun agent trouvé."
      disabled={disabled}
      buttonClassName={widthClassName}
      contentClassName="w-[420px]"
    />
  );
}
