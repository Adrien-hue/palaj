"use client";

import * as React from "react";
import { useRouter, useSearchParams } from "next/navigation";

import { EntityCombobox, type EntityComboboxItem } from "@/components/ui/entity-combobox";

type PosteListItem = {
  id: number;
  nom: string;
};

function buildHrefWithSamePeriod(pathname: string, sp: URLSearchParams) {
  const next = new URLSearchParams();
  const start = sp.get("start");
  const end = sp.get("end");
  const anchor = sp.get("anchor");

  if (start && end) {
    next.set("start", start);
    next.set("end", end);
  } else if (anchor) {
    next.set("anchor", anchor);
  }

  const qs = next.toString();
  return qs ? `${pathname}?${qs}` : pathname;
}

export function PosteHeaderSelect({
  postes,
  valueId,
  disabled,
  widthClassName = "w-[320px] sm:w-[380px]",
}: {
  postes: PosteListItem[];
  valueId: number;
  disabled?: boolean;
  widthClassName?: string;
}) {
  const router = useRouter();
  const searchParams = useSearchParams();

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
        const nextPath = `/app/planning/postes/${id}`;
        router.replace(buildHrefWithSamePeriod(nextPath, searchParams));
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
