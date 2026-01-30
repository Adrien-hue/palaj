"use client";

import * as React from "react";

import { EntityCombobox, type EntityComboboxItem } from "@/components/ui/entity-combobox";

type PosteListItem = {
  id: number;
  nom: string;
};

export function PosteHeaderSelect({
  postes,
  valueId,
  disabled,
  widthClassName = "w-[320px] sm:w-[380px]",
  onChange,
}: {
  postes: PosteListItem[];
  valueId: number | null;
  disabled?: boolean;
  widthClassName?: string;
  onChange?: (id: number | null) => void;
}) {
  const items: EntityComboboxItem[] = React.useMemo(() => {
    return postes.map((p) => ({
      id: p.id,
      label: p.nom,
      keywords: p.nom,
    }));
  }, [postes]);

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
      placeholder="Choisir un poste…"
      searchPlaceholder="Rechercher un poste…"
      emptyText="Aucun poste trouvé."
      disabled={disabled}
      buttonClassName={widthClassName}
      contentClassName="w-[420px]"
    />
  );
}
