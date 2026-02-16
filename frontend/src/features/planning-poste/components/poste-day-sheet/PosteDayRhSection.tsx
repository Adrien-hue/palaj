"use client";

import * as React from "react";

import type { RhPosteDayResponse, RhPosteDayAgent } from "@/types";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { DrawerSection, EmptyBox } from "@/components/planning/DrawerSection";
import { cn } from "@/lib/utils";

import { groupRhViolations } from "@/features/rh-validation/utils/rhViolations.group";
import { RhViolationCard } from "@/features/rh-validation/components/RhViolationCard";

import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";

function agentSortKey(a: RhPosteDayAgent) {
  if ((a.errors_count ?? 0) > 0) return 0;
  if ((a.warnings_count ?? 0) > 0) return 1;
  return 2;
}

type RhDayHookLike = {
  data?: RhPosteDayResponse;
  isLoading: boolean;
  isValidating: boolean;
  error: unknown;
};

export function PosteDayRhSection({
  rhDay,
  agentLabel,
  onRefresh,
}: {
  rhDay: RhDayHookLike;
  agentLabel: (id: number) => string;
  onRefresh: () => void;
}) {
  const agents = rhDay.data?.agents ?? [];

  // Totaux mémoïsés
  const totals = React.useMemo(() => {
    let errors = 0;
    let warnings = 0;
    let infos = 0;

    for (const a of agents) {
      errors += a.errors_count ?? 0;
      warnings += a.warnings_count ?? 0;
      infos += a.infos_count ?? 0;
    }

    return { errors, warnings, infos };
  }, [agents]);

  // Groupement violations mémoïsé par agent
  const groupsByAgentId = React.useMemo(() => {
    const m = new Map<number, ReturnType<typeof groupRhViolations>>();
    for (const a of agents) {
      m.set(a.agent_id, groupRhViolations(a.violations));
    }
    return m;
  }, [agents]);

  // Liste triée mémoïsée
  const sortedAgents = React.useMemo(() => {
    return agents.slice().sort((a, b) => {
      const r = agentSortKey(a) - agentSortKey(b);
      if (r !== 0) return r;
      return (a.agent_id ?? 0) - (b.agent_id ?? 0);
    });
  }, [agents]);

  // Option: garder un item ouvert max (type="single")
  // Si tu veux multi ouvert : type="multiple" et value:string[]
  const [openItem, setOpenItem] = React.useState<string | undefined>(undefined);

  // Reset l’accordion quand on change de journée / rechargement complet
  React.useEffect(() => {
    setOpenItem(undefined);
  }, [rhDay.data?.date]);

  return (
    <DrawerSection title="Contrôle RH">
      {rhDay.isLoading ? (
        <EmptyBox>Chargement du contrôle RH…</EmptyBox>
      ) : rhDay.error ? (
        <EmptyBox>Impossible de charger le contrôle RH.</EmptyBox>
      ) : !rhDay.data ? (
        <EmptyBox>Aucune donnée RH.</EmptyBox>
      ) : (
        <div className="space-y-3">
          {/* Résumé */}
          <div className="flex flex-wrap items-center gap-2">
            <div className="text-sm text-muted-foreground">
              {rhDay.data.eligible_agents_count} agent(s) éligible(s)
            </div>

            {totals.errors > 0 ? (
              <Badge variant="destructive" className="tabular-nums">
                Bloquants {totals.errors}
              </Badge>
            ) : null}

            {totals.warnings > 0 ? (
              <Badge variant="secondary" className="tabular-nums">
                Alertes {totals.warnings}
              </Badge>
            ) : null}

            {totals.errors === 0 && totals.warnings === 0 ? (
              <Badge variant="outline">OK</Badge>
            ) : null}

            <Button
              type="button"
              size="sm"
              variant="ghost"
              className="ml-auto"
              onClick={onRefresh}
              disabled={rhDay.isValidating}
            >
              {rhDay.isValidating ? "Actualisation…" : "Actualiser"}
            </Button>
          </div>

          {/* Liste agents */}
          {sortedAgents.length === 0 ? (
            <EmptyBox>Aucun agent éligible.</EmptyBox>
          ) : (
            <Accordion
              type="single"
              collapsible
              value={openItem}
              onValueChange={setOpenItem}
              className="space-y-2"
            >
              {sortedAgents.map((a) => {
                const blockers = a.errors_count ?? 0;
                const warnings = a.warnings_count ?? 0;

                const isBad = blockers > 0;
                const isWarn = !isBad && warnings > 0;

                const groups = groupsByAgentId.get(a.agent_id) ?? [];
                const violationsCount = a.violations?.length ?? 0;

                // value stable et unique
                const itemValue = `agent-${a.agent_id}`;

                return (
                  <AccordionItem
                    key={a.agent_id}
                    value={itemValue}
                    className={cn(
                      "rounded-lg border px-3",
                      // on évite les bordures internes de l’AccordionItem
                      "data-[state=open]:shadow-sm",
                      isBad && "border-destructive/35 bg-destructive/5",
                      isWarn && "border-amber-500/30 bg-amber-500/5",
                    )}
                  >
                    <AccordionTrigger className="py-3 hover:no-underline">
                      <div className="flex w-full items-start justify-between gap-3 pr-2">
                        <div className="min-w-0 text-left">
                          <div className="truncate text-sm font-semibold">
                            {agentLabel(a.agent_id)}
                          </div>
                          <div className="text-xs text-muted-foreground">
                            {a.is_valid ? "Valide" : "Non valide"}
                            <span className="ml-2">
                              · {violationsCount} détail(s)
                            </span>
                          </div>
                        </div>

                        <div className="flex shrink-0 items-center gap-2">
                          {blockers > 0 ? (
                            <Badge
                              variant="destructive"
                              className="h-6 rounded-full px-2 text-xs font-medium tabular-nums"
                              title={`${blockers} violation(s) bloquante(s)`}
                            >
                              {blockers}
                            </Badge>
                          ) : warnings > 0 ? (
                            <Badge
                              variant="secondary"
                              className="h-6 rounded-full px-2 text-xs font-medium tabular-nums"
                              title={`${warnings} alerte(s)`}
                            >
                              {warnings}
                            </Badge>
                          ) : (
                            <Badge
                              variant="outline"
                              className="h-6 rounded-full px-2 text-xs font-medium"
                              title="Aucune violation"
                            >
                              OK
                            </Badge>
                          )}
                        </div>
                      </div>
                    </AccordionTrigger>

                    <AccordionContent className="pb-3">
                      <div className="space-y-2">
                        {groups.length ? (
                          groups.map((g) => (
                            <RhViolationCard
                              key={g.key}
                              severity={g.severity}
                              title={
                                (g.rule && g.rule.trim().length > 0
                                  ? g.rule
                                  : g.code) ?? ""
                              }
                              message={g.message}
                              rangeLabel={g.range.label}
                              count={g.count}
                            />
                          ))
                        ) : (
                          <div className="text-sm text-muted-foreground">
                            Aucune violation.
                          </div>
                        )}
                      </div>
                    </AccordionContent>
                  </AccordionItem>
                );
              })}
            </Accordion>
          )}
        </div>
      )}
    </DrawerSection>
  );
}
