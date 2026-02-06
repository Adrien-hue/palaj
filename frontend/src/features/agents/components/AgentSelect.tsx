"use client";

import { useId, useMemo, useState } from "react";
import type { Agent } from "@/types";

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
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { cn } from "@/lib/utils";

import { DayTypeBadge } from "@/components/planning/DayTypeBadge";
import type {
  AgentSelectStatus,
  AgentSelectStatusById,
} from "./agentSelect.types";

type Props = {
  onChange: (v: number | null) => void;

  agents: Agent[];
  disabled?: boolean;

  statusByAgentId?: AgentSelectStatusById;

  /** UI */
  label?: string | null;
  className?: string;

  placeholder?: string;
  emptyLabel?: string;

  allowClear?: boolean;
  clearLabel?: string;
};

function isWorkingStatus(
  s: AgentSelectStatus | undefined,
): s is {
  dayType: "working";
  trancheLabel?: string;
  trancheColor?: string | null;
} {
  return !!s && s.dayType === "working";
}

function norm(s: string) {
  return s
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "");
}

type PreparedAgent = Agent & { __hay: string; __sort: string };

export function AgentSelect({
  onChange,
  agents,
  disabled,
  statusByAgentId,

  label = "Ajouter un agent",
  className,

  placeholder = "Sélectionner un agent…",
  emptyLabel = "Aucun agent disponible",

  allowClear = false,
  clearLabel = "Aucun (vider)",
}: Props) {
  const id = useId();
  const [q, setQ] = useState("");
  const [internalValue, setInternalValue] = useState<string>("");

  const prepared = useMemo<PreparedAgent[]>(() => {
    const base = agents.map((a) => {
      const sortKey = `${a.nom ?? ""} ${a.prenom ?? ""}`.trim().toLowerCase();
      const hay = norm(
        `${a.prenom ?? ""} ${a.nom ?? ""} ${a.code_personnel ?? ""}`.trim(),
      );
      return Object.assign(a, { __hay: hay, __sort: sortKey });
    });

    base.sort((a, b) => {
      if (a.actif !== b.actif) return a.actif ? -1 : 1;
      return a.__sort.localeCompare(b.__sort, "fr");
    });

    return base;
  }, [agents]);

  const filtered = useMemo(() => {
    const query = norm(q.trim());
    if (!query) return prepared;
    return prepared.filter((a) => a.__hay.includes(query));
  }, [prepared, q]);

  const isEmpty = filtered.length === 0;

  return (
    <div className={cn("space-y-2", className)}>
      {label ? (
        <Label htmlFor={id} className="text-xs text-muted-foreground">
          {label}
        </Label>
      ) : null}

      <Select
        value={internalValue || undefined}
        onOpenChange={(o) => {
          if (!o) setQ("");
        }}
        onValueChange={(v) => {
          if (!v || v === "__clear__") {
            onChange(null);
            setInternalValue("");
            return;
          }
          onChange(Number(v));
          setInternalValue("");
        }}
        disabled={disabled}
      >
        <SelectTrigger id={id} className="w-full">
          <SelectValue placeholder={placeholder} />
        </SelectTrigger>

        <SelectContent>
          <div className="p-2 pb-1">
            <Input
              value={q}
              onChange={(e) => setQ(e.target.value)}
              placeholder="Rechercher (nom, prénom, matricule)…"
              className="h-9"
            />
          </div>

          <ScrollArea className="h-72">
            {isEmpty ? (
              <div className="px-2 py-2 text-sm text-muted-foreground">
                {emptyLabel}
              </div>
            ) : (
              <SelectGroup>
                <SelectLabel className="text-xs">Agents</SelectLabel>

                {filtered.map((a) => {
                  const status = statusByAgentId?.get(a.id);

                  const statusChip =
                    isWorkingStatus(status) && status.trancheLabel ? (
                      <span className="inline-flex max-w-[160px] items-center gap-1 rounded-full border px-2 py-0.5 text-[11px] text-muted-foreground">
                        <span
                          className="h-2 w-2 shrink-0 rounded-full border"
                          style={{
                            backgroundColor:
                              status.trancheColor ?? "transparent",
                          }}
                          aria-hidden="true"
                        />
                        <span className="min-w-0 truncate">
                          {status.trancheLabel}
                        </span>
                      </span>
                    ) : status ? (
                      <DayTypeBadge dayType={status.dayType} />
                    ) : null;

                  return (
                    <SelectItem key={a.id} value={String(a.id)}>
                      <div className="flex w-full items-center justify-between gap-2">
                        <span className="min-w-0 flex-1 truncate">
                          {a.prenom} {a.nom}
                          {a.code_personnel ? ` (${a.code_personnel})` : ""}
                        </span>

                        <div className="flex shrink-0 items-center gap-2">
                          {statusChip}

                          {!a.actif ? (
                            <span className="shrink-0 rounded-full border px-2 py-0.5 text-[10px] text-muted-foreground">
                              Inactif
                            </span>
                          ) : null}
                        </div>
                      </div>
                    </SelectItem>
                  );
                })}
              </SelectGroup>
            )}

            {allowClear ? (
              <SelectGroup>
                <SelectLabel className="text-xs">Actions</SelectLabel>
                <SelectItem value="__clear__">{clearLabel}</SelectItem>
              </SelectGroup>
            ) : null}
          </ScrollArea>
        </SelectContent>
      </Select>
    </div>
  );
}
