"use client";

import { AgentDayVm } from "../vm/agentPlanning.vm";
import { formatDateFR } from "@/utils/date.format";
import { AgentDayGantt } from "./AgentDayGantt";

import { Badge } from "@/components/ui/badge";

import { DayTypeBadge } from "@/components/planning/DayTypeBadge";
import { DrawerSection, EmptyBox } from "@/components/planning/DrawerSection";
import { PlanningSheetShell } from "@/components/planning/PlanningSheetShell";

export function AgentDaySheet({
  open,
  onClose,
  selectedDay,
  posteNameById,
}: {
  open: boolean;
  onClose: () => void;
  selectedDay: AgentDayVm | null;
  posteNameById: Map<number, string>;
}) {
  const dateLabel = selectedDay ? formatDateFR(selectedDay.day_date) : "Jour";

  return (
    <PlanningSheetShell
      open={open}
      onOpenChange={(o) => {
        if (!o) onClose();
      }}
      headerVariant="sticky"
      contentClassName="w-full p-0 sm:max-w-lg"
      rootClassName="bg-[color:var(--app-bg)]"
      bodyClassName="p-4"
      title={
        <span className="flex min-w-0 items-center gap-2">
          <span className="truncate">{dateLabel}</span>
          {selectedDay ? <DayTypeBadge dayType={selectedDay.day_type} /> : null}
        </span>
      }
      description={<span className="truncate">Planning du jour</span>}
    >
      <div className="space-y-4">
        {/* Timeline */}
        <DrawerSection
          variant="surface"
          title="Timeline"
          subtitle="Vue synthétique des tranches."
        >
          {selectedDay ? (
            <AgentDayGantt
              segments={selectedDay.segments}
              posteNameById={posteNameById}
              dayStart="00:00:00"
              dayEnd="23:59:00"
            />
          ) : (
            <EmptyBox>Aucun jour sélectionné.</EmptyBox>
          )}
        </DrawerSection>

        {/* Tranches */}
        <DrawerSection
          variant="surface"
          title="Tranches"
          subtitle="Détail des affectations par poste."
        >
          {!selectedDay || selectedDay.segments.length === 0 ? (
            <EmptyBox>Aucune tranche</EmptyBox>
          ) : (
            <div className="space-y-2">
              {selectedDay.segments.map((seg) => {
                const poste =
                  posteNameById.get(seg.posteId) ?? `Poste #${seg.posteId}`;
                const time = `${seg.start.slice(0, 5)}–${seg.end.slice(0, 5)}`;

                return (
                  <div
                    key={seg.key}
                    className="rounded-xl border border-[color:var(--app-border)] bg-[color:var(--app-bg)] p-3"
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div className="min-w-0">
                        <div className="truncate text-sm font-semibold text-[color:var(--app-text)]">
                          {seg.nom}
                          {seg.continuesPrev ? " ←" : ""}
                          {seg.continuesNext ? " →" : ""}
                        </div>
                        <div className="truncate text-xs text-[color:var(--app-muted)]">
                          {poste}
                        </div>
                      </div>

                      <Badge variant="outline" className="shrink-0 tabular-nums">
                        {time}
                      </Badge>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </DrawerSection>
      </div>
    </PlanningSheetShell>
  );
}
