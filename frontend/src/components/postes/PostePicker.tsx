"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { Check, ChevronsUpDown, Clock } from "lucide-react";

import type { Poste } from "@/types/postes";
import { cn } from "@/lib/utils";

import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
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

const RECENTS_KEY = "palaj.recents.postes";

/* ───────────────────────── helpers ───────────────────────── */

function posteLabel(p: Poste) {
  return p.nom ?? `Poste #${p.id}`;
}

function normalize(s: string) {
  return s
    .toLowerCase()
    .normalize("NFD")
    .replace(/\p{Diacritic}/gu, "");
}

function loadRecents(): Poste[] {
  try {
    const raw = localStorage.getItem(RECENTS_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw) as Poste[];
    if (!Array.isArray(parsed)) return [];
    return parsed.slice(0, 8);
  } catch {
    return [];
  }
}

function saveRecent(poste: Poste) {
  try {
    const current = loadRecents();
    const next = [poste, ...current.filter((p) => p.id !== poste.id)].slice(
      0,
      8
    );
    localStorage.setItem(RECENTS_KEY, JSON.stringify(next));
  } catch {
    // ignore
  }
}

function searchValue(p: Poste) {
  return normalize(`${p.nom ?? ""} ${p.id ?? ""}`);
}

/* ───────────────────────── component ───────────────────────── */

export function PostePicker({
  postes,
  isLoading,
  selectedId: controlledSelectedId,
  onPick: onPickProp,
}: {
  postes: Poste[];
  isLoading?: boolean;
  selectedId?: number | null;
  onPick?: (poste: Poste) => void;
}) {
  const router = useRouter();

  const [open, setOpen] = React.useState(false);
  const [recents, setRecents] = React.useState<Poste[]>([]);
  const [selectedId, setSelectedId] = React.useState<number | null>(null);

  const effectiveSelectedId = controlledSelectedId ?? selectedId;

  React.useEffect(() => {
    setRecents(loadRecents());
  }, []);

  const selectedPoste = React.useMemo(
    () =>
      effectiveSelectedId
        ? postes.find((p) => p.id === effectiveSelectedId) ?? null
        : null,
    [postes, effectiveSelectedId]
  );

  function onPick(p: Poste) {
    saveRecent(p);
    setRecents(loadRecents());

    if (controlledSelectedId == null) {
      setSelectedId(p.id);
    }

    setOpen(false);

    if (onPickProp) {
      onPickProp(p);
    } else {
      router.push(`/app/planning/postes/${p.id}`);
    }
  }

  return (
    <div className="space-y-3">
      <div className="text-sm text-[color:var(--app-muted)]">
        {postes.length} poste{postes.length > 1 ? "s" : ""}
      </div>

      <Popover
        open={open}
        onOpenChange={(o) => {
          setOpen(o);
        }}
      >
        <PopoverTrigger asChild>
          <Button
            variant="outline"
            role="combobox"
            aria-expanded={open}
            className="w-full justify-between border-[color:var(--app-border)] bg-[color:var(--app-surface)] text-[color:var(--app-text)]"
          >
            <span className="truncate">
              {selectedPoste ? posteLabel(selectedPoste) : "Sélectionner un poste…"}
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
            <CommandInput placeholder="Rechercher… (nom du poste)" />

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
                    {recents.map((p) => (
                      <CommandItem
                        key={`recent-${p.id}`}
                        value={searchValue(p)}
                        onSelect={() => onPick(p)}
                        className="gap-3"
                      >
                        <span className="grid h-8 w-8 shrink-0 place-items-center rounded-lg bg-[color:var(--app-soft)] ring-1 ring-[color:var(--app-border)]">
                          <span className="text-[11px] font-semibold text-[color:var(--app-soft-text)]">
                            {posteLabel(p).slice(0, 2).toUpperCase()}
                          </span>
                        </span>

                        <div className="min-w-0 flex-1">
                          <div className="flex items-center gap-2">
                            <span className="truncate text-sm font-medium">
                              {posteLabel(p)}
                            </span>
                            <Clock className="h-3.5 w-3.5 opacity-60" />
                          </div>

                          <div className="truncate text-xs text-[color:var(--app-muted)]">
                            ID: {p.id}
                          </div>
                        </div>

                        <Check
                          className={cn(
                            "ml-2 h-4 w-4",
                            effectiveSelectedId === p.id ? "opacity-100" : "opacity-0"
                          )}
                        />
                      </CommandItem>
                    ))}
                  </CommandGroup>
                  <CommandSeparator />
                </>
              ) : null}

              <CommandGroup heading="Postes">
                {postes.map((p) => (
                  <CommandItem
                    key={p.id}
                    value={searchValue(p)}
                    onSelect={() => onPick(p)}
                    className="gap-3"
                  >
                    <span className="grid h-8 w-8 shrink-0 place-items-center rounded-lg bg-[color:var(--app-soft)] ring-1 ring-[color:var(--app-border)]">
                      <span className="text-[11px] font-semibold text-[color:var(--app-soft-text)]">
                        {posteLabel(p).slice(0, 2).toUpperCase()}
                      </span>
                    </span>

                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2">
                        <span className="truncate text-sm font-medium">
                          {posteLabel(p)}
                        </span>
                      </div>
                    </div>

                    <Check
                      className={cn(
                        "ml-2 h-4 w-4",
                        effectiveSelectedId === p.id ? "opacity-100" : "opacity-0"
                      )}
                    />
                  </CommandItem>
                ))}
              </CommandGroup>

              {postes.length > 250 ? (
                <div className="border-t p-3 text-xs text-[color:var(--app-muted)]">
                  Beaucoup de résultats ({postes.length}). Une recherche serveur pourra améliorer les perfs.
                </div>
              ) : null}
            </CommandList>
          </Command>
        </PopoverContent>
      </Popover>

      <div className="text-xs text-[color:var(--app-muted)]">
        Astuce : tape un nom de poste pour filtrer rapidement.
      </div>
    </div>
  );
}
