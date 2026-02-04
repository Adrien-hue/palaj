"use client";

import { useMemo, useId } from "react";
import type { Tranche } from "@/types";
import { useQualifiedTranches } from "@/features/planning-agent/hooks/useQualifiedTranches";

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

  label = "Tranche",
  className,

  placeholder = "Choisir une tranche",
  emptyLabel = "Aucune tranche disponible",
  loadingLabel = "Chargement des tranches…",
  errorLabel = "Erreur de chargement",
}: Props) {
  const id = useId();
  const { tranches, isLoading, error } = useQualifiedTranches(agentId);

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

  const stringValue = value === null ? undefined : String(value);
  const isDisabled = disabled || isLoading;

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
          <SelectValue placeholder={isLoading ? loadingLabel : placeholder} />
        </SelectTrigger>

        <SelectContent>
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
                      {trs.map((t) => (
                        <SelectItem key={t.id} value={String(t.id)}>
                          <div className="flex items-center gap-2">
                            <span
                              className="h-2.5 w-2.5 shrink-0 rounded-full border"
                              style={{
                                backgroundColor: t.color ?? "transparent",
                              }}
                              aria-hidden="true"
                            />
                            <span className="truncate">
                              {t.nom} ({t.heure_debut.slice(0, 5)}–
                              {t.heure_fin.slice(0, 5)})
                            </span>
                          </div>
                        </SelectItem>
                      ))}
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
