"use client";

import * as React from "react";

import { EntityCombobox, type EntityComboboxItem } from "@/components/ui/entity-combobox";
import { Team } from "@/types";

export function TeamHeaderSelect({
  teams,
  valueId,
  disabled,
  widthClassName = "w-[320px] sm:w-[380px]",
  onChange,
}: {
  teams: Team[];
  valueId: number | null;
  disabled?: boolean;
  widthClassName?: string;
  onChange?: (id: number | null) => void;
}) {

  const items: EntityComboboxItem[] = React.useMemo(() => {
    return teams
      .map((a) => ({
        id: a.id,
        label: `${a.name}`,
        description: a.description ?? undefined,
        keywords: `${a.name} ${a.description ?? ""}`,
      }));
  }, [teams]);

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
      placeholder="Choisir une équipe…"
      searchPlaceholder="Rechercher une équipe…"
      emptyText="Aucune équipe trouvée."
      disabled={disabled}
      buttonClassName={widthClassName}
      contentClassName="w-[420px]"
    />
  );
}
