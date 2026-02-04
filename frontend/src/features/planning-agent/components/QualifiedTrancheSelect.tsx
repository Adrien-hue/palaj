"use client";

import { useEffect, useMemo, useId, useRef } from "react";
import type { Tranche } from "@/types";
import { useQualifiedTranches } from "@/features/planning-agent/hooks/useQualifiedTranches";
import { useCoveredTrancheIds } from "@/features/planning-agent/hooks/useCoveredTrancheIds";

import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectLabel,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Label } from "@/components/ui/label";
import { cn } from "@/lib/utils";

type Props = {
  agentId: number;
  value: number | null;
  onChange: (v: number | null) => void;
  posteNameById: Map<number, string>;
  disabled?: boolean;

  dateISO: string | null;
  refreshKey?: number;

  /** UI */
  label?: string | null;
  className?: string;

  placeholder?: string;
  emptyLabel?: string;
  loadingLabel?: string;
  errorLabel?: string;
};

export function QualifiedTrancheSelect({
  agentId,
  value,
  onChange,
  posteNameById,
  disabled,
  dateISO,
  refreshKey,

  label = "Tranche",
  className,

  placeholder = "Choisir une tranche",
  emptyLabel = "Aucune tranche disponible",
  loadingLabel = "Chargement des tranches…",
  errorLabel = "Erreur de chargement",
}: Props) {
  const id = useId();

  const { tranches, isLoading, error, posteIds } = useQualifiedTranches(agentId);

  const {
    coveredTrancheIds,
    isLoading: loadingCoverage,
    refreshCoverage,
  } = useCoveredTrancheIds({ dateISO, posteIds });

  // clé stable dérivée des posteIds
  const posteIdsKey = useMemo(() => posteIds.join(","), [posteIds]);

  // ne refresh que si refreshKey a réellement changé
  const lastAppliedRefreshKey = useRef<number | undefined>(undefined);

  useEffect(() => {
    if (refreshKey === undefined) return;
    if (!dateISO) return;
    if (posteIds.length === 0) return;

    if (lastAppliedRefreshKey.current === refreshKey) return;
    lastAppliedRefreshKey.current = refreshKey;

    refreshCoverage();
  }, [refreshKey, dateISO, posteIdsKey, posteIds.length, refreshCoverage]);

  const grouped = useMemo(() => {
    const map = new Map<number, Tranche[]>();

    for (const t of tranches ?? []) {
      if (!map.has(t.poste_id)) map.set(t.poste_id, []);
      map.get(t.poste_id)!.push(t);
    }

    for (const arr of map.values()) {
      arr.sort((a, b) => a.heure_debut.localeCompare(b.heure_debut));
    }

    return [...map.entries()].sort(([a], [b]) => a - b);
  }, [tranches]);

  // Force remount du menu quand la couverture change / refresh
  const contentKey = `${refreshKey ?? 0}-${coveredTrancheIds.size}`;

  const stringValue = value === null ? undefined : String(value);
  const isDisabled = disabled || isLoading || loadingCoverage;

  return (
    <div className={cn("space-y-1", className)}>
      {label ? (
        <Label htmlFor={id} className="text-xs text-muted-foreground">
          {label}
        </Label>
      ) : null}

      <Select
        value={stringValue}
        onValueChange={(v) => {
          if (!v || v === "__clear__") return onChange(null);
          onChange(Number(v));
        }}
        disabled={isDisabled}
      >
        <SelectTrigger id={id} className="w-full">
          <SelectValue
            placeholder={
              isLoading || loadingCoverage ? loadingLabel : placeholder
            }
          />
        </SelectTrigger>

        <SelectContent key={contentKey}>
          <ScrollArea className="h-72">
            {error ? (
              <div className="px-2 py-2 text-sm text-destructive">
                {errorLabel}
              </div>
            ) : null}

            {!isLoading && !error && grouped.length === 0 ? (
              <div className="px-2 py-2 text-sm text-muted-foreground">
                {emptyLabel}
              </div>
            ) : null}

            {!isLoading && !error
              ? grouped.map(([posteId, trs]) => {
                  const posteName =
                    posteNameById.get(posteId) ?? `Poste #${posteId}`;

                  return (
                    <SelectGroup key={posteId}>
                      <SelectLabel className="text-xs">{posteName}</SelectLabel>

                      {trs.map((t) => {
                        const isCovered = coveredTrancheIds.has(t.id);

                        return (
                          <SelectItem
                            key={`${t.id}-${isCovered ? "covered" : "open"}`}
                            value={String(t.id)}
                            className={cn(
                              "flex items-center",
                              isCovered && "opacity-70"
                            )}
                          >
                            <div className="flex w-full items-center gap-2">
                              <span
                                className="h-2.5 w-2.5 shrink-0 rounded-full border"
                                style={{
                                  backgroundColor: t.color ?? "transparent",
                                }}
                                aria-hidden="true"
                              />
                              <span className="min-w-0 flex-1 truncate">
                                {t.nom} ({t.heure_debut.slice(0, 5)}–
                                {t.heure_fin.slice(0, 5)})
                              </span>

                              {isCovered ? (
                                <span className="shrink-0 rounded-full border px-2 py-0.5 text-[10px] text-muted-foreground">
                                  Couvert
                                </span>
                              ) : null}
                            </div>
                          </SelectItem>
                        );
                      })}
                    </SelectGroup>
                  );
                })
              : null}

            {!isLoading ? (
              <SelectGroup>
                <SelectLabel className="text-xs">Actions</SelectLabel>
                <SelectItem value="__clear__">Aucune (vider)</SelectItem>
              </SelectGroup>
            ) : null}
          </ScrollArea>
        </SelectContent>
      </Select>
    </div>
  );
}
