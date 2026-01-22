"use client";

import * as React from "react";
import { useRouter } from "next/navigation";

import type { Agent } from "@/types";

import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { RecentCombobox } from "@/components/pickers/RecentCombobox";

const RECENTS_KEY = "palaj.recents.agents";

/* ───────────────────────── helpers ───────────────────────── */

function agentLabel(a: Agent) {
  return `${a.prenom} ${a.nom}`;
}

function initials(a: Agent) {
  const p = (a.prenom ?? "").trim();
  const n = (a.nom ?? "").trim();
  return `${p ? p[0] : ""}${n ? n[0] : ""}`.toUpperCase() || "•";
}

function normalize(s: string) {
  return s
    .toLowerCase()
    .normalize("NFD")
    .replace(/\p{Diacritic}/gu, "");
}

function formatMeta(a: Agent) {
  const parts: string[] = [];
  if (a.code_personnel) parts.push(a.code_personnel);
  return parts.join(" • ");
}

function searchValue(a: Agent) {
  return normalize(
    `${a.prenom ?? ""} ${a.nom ?? ""} ${a.code_personnel ?? ""} ${a.id ?? ""}`
  );
}

function LeadingAvatar({ a }: { a: Agent }) {
  return (
    <span className="grid h-8 w-8 shrink-0 place-items-center rounded-lg bg-[color:var(--app-soft)] ring-1 ring-[color:var(--app-border)]">
      <span className="text-[11px] font-semibold text-[color:var(--app-soft-text)]">
        {initials(a)}
      </span>
    </span>
  );
}

/* ───────────────────────── component ───────────────────────── */

export function AgentPicker({
  agents,
  isLoading,
  selectedId,
  onPick,
}: {
  agents: Agent[];
  isLoading?: boolean;
  selectedId?: number | null;
  onPick?: (agent: Agent) => void;
}) {
  const router = useRouter();

  const [includeInactive, setIncludeInactive] = React.useState(false);

  const pool = React.useMemo(() => {
    return includeInactive ? agents : agents.filter((a) => a.actif !== false);
  }, [agents, includeInactive]);

  return (
    <div className="space-y-3">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="text-sm text-[color:var(--app-muted)]">
          {agents.length} agent{agents.length > 1 ? "s" : ""}
        </div>

        <div className="flex items-center gap-2">
          <Switch
            id="include-inactive"
            checked={includeInactive}
            onCheckedChange={setIncludeInactive}
          />
          <Label
            htmlFor="include-inactive"
            className="cursor-pointer text-xs text-[color:var(--app-muted)]"
          >
            Inclure les inactifs
          </Label>
        </div>
      </div>

      <RecentCombobox<Agent>
        items={pool}
        storageKey={RECENTS_KEY}
        selectedId={selectedId ?? null}
        placeholder="Sélectionner un agent…"
        searchPlaceholder="Rechercher… (nom, matricule)"
        recentsLabel="Récemment consultés"
        listLabel="Agents"
        emptyLabel={isLoading ? "Chargement…" : "Aucun résultat."}
        getId={(a) => a.id}
        getSearchValue={(a) => searchValue(a)}
        renderLeading={(a) => <LeadingAvatar a={a} />}
        renderTitle={(a) => (
          <span className="flex items-center gap-2 min-w-0">
            <span className="truncate">{agentLabel(a)}</span>
            {a.actif === false ? (
              <Badge variant="secondary" className="rounded-full text-[11px]">
                Inactif
              </Badge>
            ) : null}
          </span>
        )}
        renderSubtitle={(a) => {
          const meta = formatMeta(a);
          return meta ? meta : `ID: ${a.id}`;
        }}
        onPick={(a) => {
          if (onPick) return onPick(a);
          router.push(`/app/planning/agents/${a.id}`);
        }}
        disabled={isLoading}
      />

      <div className="text-xs text-[color:var(--app-muted)]">
        Astuce : tape un nom, un prénom ou un matricule pour filtrer rapidement.
      </div>
    </div>
  );
}
