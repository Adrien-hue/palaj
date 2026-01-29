"use client";

import * as React from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";

import { EntityCombobox, type EntityComboboxItem } from "@/components/ui/entity-combobox";

type AgentListItem = {
  id: number;
  nom: string;
  prenom: string;
  code_personnel?: string | null;
  actif: boolean;
};

function buildHrefWithSamePeriod(pathname: string, sp: URLSearchParams) {
  // on conserve uniquement les params de période
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

export function AgentHeaderSelect({
  agents,
  valueId,
  disabled,
  widthClassName = "w-[320px] sm:w-[380px]",
}: {
  agents: AgentListItem[];
  valueId: number;
  disabled?: boolean;
  widthClassName?: string;
}) {
  const router = useRouter();
  const searchParams = useSearchParams();

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
        const nextPath = `/app/planning/agents/${id}`;
        router.replace(buildHrefWithSamePeriod(nextPath, searchParams));
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
