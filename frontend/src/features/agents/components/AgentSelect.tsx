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

type Props = {
  onChange: (v: number | null) => void;

  agents: Agent[];
  disabled?: boolean;

  /** UI */
  label?: string | null;
  className?: string;

  placeholder?: string;
  emptyLabel?: string;

  allowClear?: boolean;
  clearLabel?: string;
};

function norm(s: string) {
  return s
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "");
}

export function AgentSelect({
  onChange,
  agents,
  disabled,

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

  const sortedAgents = useMemo(() => {
    const base = agents.slice();
    base.sort((a, b) => {
      if (a.actif !== b.actif) return a.actif ? -1 : 1;
      const an = `${a.nom} ${a.prenom}`.toLowerCase();
      const bn = `${b.nom} ${b.prenom}`.toLowerCase();
      return an.localeCompare(bn, "fr");
    });
    return base;
  }, [agents]);

  const filtered = useMemo(() => {
    const query = norm(q.trim());
    if (!query) return sortedAgents;

    return sortedAgents.filter((a) => {
      const hay = norm(`${a.prenom} ${a.nom} ${a.code_personnel ?? ""}`.trim());
      return hay.includes(query);
    });
  }, [sortedAgents, q]);

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
          setInternalValue(""); // reset visuel
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

                {filtered.map((a) => (
                  <SelectItem key={a.id} value={String(a.id)}>
                    <div className="flex w-full items-center justify-between gap-2">
                      <span className="min-w-0 flex-1 truncate">
                        {a.prenom} {a.nom}
                        {a.code_personnel ? ` (${a.code_personnel})` : ""}
                      </span>

                      {!a.actif ? (
                        <span className="shrink-0 rounded-full border px-2 py-0.5 text-[10px] text-muted-foreground">
                          Inactif
                        </span>
                      ) : null}
                    </div>
                  </SelectItem>
                ))}
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
