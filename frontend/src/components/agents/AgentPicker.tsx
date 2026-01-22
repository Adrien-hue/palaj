"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { Check, ChevronsUpDown, Clock } from "lucide-react";

import type { Agent } from "@/types";
import { cn } from "@/lib/utils";

import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
  CommandSeparator,
} from "@/components/ui/command";

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

function formatMeta(a: Agent) {
  const parts: string[] = [];
  if (a.code_personnel) parts.push(a.code_personnel);
  return parts.join(" • ");
}

function normalize(s: string) {
  return s
    .toLowerCase()
    .normalize("NFD")
    .replace(/\p{Diacritic}/gu, "");
}

function loadRecents(): Agent[] {
  try {
    const raw = localStorage.getItem(RECENTS_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw) as Agent[];
    if (!Array.isArray(parsed)) return [];
    return parsed.slice(0, 8);
  } catch {
    return [];
  }
}

function saveRecent(agent: Agent) {
  try {
    const current = loadRecents();
    const next = [agent, ...current.filter((a) => a.id !== agent.id)].slice(
      0,
      8
    );
    localStorage.setItem(RECENTS_KEY, JSON.stringify(next));
  } catch {
    // ignore
  }
}

function searchValue(a: Agent) {
  return normalize(
    `${a.prenom ?? ""} ${a.nom ?? ""} ${a.code_personnel ?? ""} ${a.id ?? ""}`
  );
}

/* ───────────────────────── component ───────────────────────── */

export function AgentPicker({
  agents,
  isLoading,
  selectedId: controlledSelectedId,
  onPick: onPickProp,
}: {
  agents: Agent[];
  isLoading?: boolean;
  selectedId?: number | null;
  onPick?: (agent: Agent) => void;
}) {
  const router = useRouter();

  const [open, setOpen] = React.useState(false);
  const [includeInactive, setIncludeInactive] = React.useState(false);
  const [recents, setRecents] = React.useState<Agent[]>([]);
  const [selectedId, setSelectedId] = React.useState<number | null>(null);

  const effectiveSelectedId = controlledSelectedId ?? selectedId;

  React.useEffect(() => {
    setRecents(loadRecents());
  }, []);

  const pool = React.useMemo(() => {
    return includeInactive
      ? agents
      : agents.filter((a) => a.actif !== false);
  }, [agents, includeInactive]);

  const selectedAgent = React.useMemo(
    () =>
      effectiveSelectedId
        ? agents.find((a) => a.id === effectiveSelectedId) ?? null
        : null,
    [agents, effectiveSelectedId]
  );

  function onPick(a: Agent) {
    saveRecent(a);
    setRecents(loadRecents());

    if (controlledSelectedId == null) {
      setSelectedId(a.id);
    }

    setOpen(false);

    if (onPickProp) {
      onPickProp(a);
    } else {
      router.push(`/app/planning/agents/${a.id}`);
    }
  }

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

      {/* Combobox */}
      <Popover open={open} onOpenChange={setOpen}>
        <PopoverTrigger asChild>
          <Button
            variant="outline"
            role="combobox"
            aria-expanded={open}
            className="w-full justify-between border-[color:var(--app-border)] bg-[color:var(--app-surface)] text-[color:var(--app-text)]"
          >
            <span className="truncate">
              {selectedAgent
                ? agentLabel(selectedAgent)
                : "Sélectionner un agent…"}
            </span>
            <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-60" />
          </Button>
        </PopoverTrigger>

        <PopoverContent
          align="start"
          sideOffset={4}
          className="w-[--radix-popover-trigger-width] p-0"
        >
          <Command>
            <CommandInput placeholder="Rechercher… (nom, matricule)" />

            <CommandList className="max-h-80">
              {isLoading ? (
                <div className="p-3 text-sm text-[color:var(--app-muted)]">
                  Chargement…
                </div>
              ) : null}

              <CommandEmpty>Aucun résultat.</CommandEmpty>

              {recents.length > 0 ? (
                <>
                  <CommandGroup heading="Récemment consultés">
                    {recents
                      .filter((a) =>
                        includeInactive ? true : a.actif !== false
                      )
                      .map((a) => {
                        const meta = formatMeta(a);
                        const inactive = a.actif === false;

                        return (
                          <CommandItem
                            key={`recent-${a.id}`}
                            value={searchValue(a)}
                            onSelect={() => onPick(a)}
                            className="gap-3"
                          >
                            <span className="grid h-8 w-8 shrink-0 place-items-center rounded-lg bg-[color:var(--app-soft)] ring-1 ring-[color:var(--app-border)]">
                              <span className="text-[11px] font-semibold text-[color:var(--app-soft-text)]">
                                {initials(a)}
                              </span>
                            </span>

                            <div className="min-w-0 flex-1">
                              <div className="flex items-center gap-2">
                                <span className="truncate text-sm font-medium">
                                  {agentLabel(a)}
                                </span>
                                {inactive ? (
                                  <Badge
                                    variant="secondary"
                                    className="rounded-full text-[11px]"
                                  >
                                    Inactif
                                  </Badge>
                                ) : null}
                                <Clock className="h-3.5 w-3.5 opacity-60" />
                              </div>

                              {meta ? (
                                <div className="truncate text-xs text-[color:var(--app-muted)]">
                                  {meta}
                                </div>
                              ) : null}
                            </div>

                            <Check
                              className={cn(
                                "ml-2 h-4 w-4",
                                effectiveSelectedId === a.id
                                  ? "opacity-100"
                                  : "opacity-0"
                              )}
                            />
                          </CommandItem>
                        );
                      })}
                  </CommandGroup>
                  <CommandSeparator />
                </>
              ) : null}

              <CommandGroup heading="Agents">
                {pool.map((a) => {
                  const meta = formatMeta(a);
                  const inactive = a.actif === false;

                  return (
                    <CommandItem
                      key={a.id}
                      value={searchValue(a)}
                      onSelect={() => onPick(a)}
                      className="gap-3"
                    >
                      <span className="grid h-8 w-8 shrink-0 place-items-center rounded-lg bg-[color:var(--app-soft)] ring-1 ring-[color:var(--app-border)]">
                        <span className="text-[11px] font-semibold text-[color:var(--app-soft-text)]">
                          {initials(a)}
                        </span>
                      </span>

                      <div className="min-w-0 flex-1">
                        <div className="flex items-center gap-2">
                          <span className="truncate text-sm font-medium">
                            {agentLabel(a)}
                          </span>
                          {inactive ? (
                            <Badge
                              variant="secondary"
                              className="rounded-full text-[11px]"
                            >
                              Inactif
                            </Badge>
                          ) : null}
                        </div>

                        {meta ? (
                          <div className="truncate text-xs text-[color:var(--app-muted)]">
                            {meta}
                          </div>
                        ) : null}
                      </div>

                      <Check
                        className={cn(
                          "ml-2 h-4 w-4",
                          effectiveSelectedId === a.id
                            ? "opacity-100"
                            : "opacity-0"
                        )}
                      />
                    </CommandItem>
                  );
                })}
              </CommandGroup>

              {pool.length > 250 ? (
                <div className="border-t p-3 text-xs text-[color:var(--app-muted)]">
                  Beaucoup de résultats ({pool.length}). Une recherche serveur
                  pourra améliorer les perfs.
                </div>
              ) : null}
            </CommandList>
          </Command>
        </PopoverContent>
      </Popover>

      <div className="text-xs text-[color:var(--app-muted)]">
        Astuce : tape un nom, un prénom ou un matricule pour filtrer rapidement.
      </div>
    </div>
  );
}
