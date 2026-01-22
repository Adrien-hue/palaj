"use client";

import { X } from "lucide-react";

import { AgentDayVm } from "../vm/agentPlanning.vm";
import { formatDateFR } from "@/utils/date.format";
import { AgentDayGantt } from "./AgentDayGantt";

import {
  Sheet,
  SheetClose,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
} from "@/components/ui/sheet";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";

function dayTypeLabel(dayType: string) {
  return dayType === "working"
    ? "Travail"
    : dayType === "rest"
    ? "Repos"
    : dayType === "absence"
    ? "Absence"
    : dayType === "unknown"
    ? "—"
    : dayType;
}

function dayTypeDotColor(dayType: string) {
  if (dayType === "working") return "var(--palaj-l)";
  if (dayType === "absence") return "var(--palaj-a)";
  if (dayType === "rest") return "var(--app-muted)";
  return "var(--app-muted)";
}

function DayTypeBadge({ dayType }: { dayType: string }) {
  return (
    <Badge variant="outline" className="rounded-full px-2 py-0.5 text-[11px] font-medium">
      <span className="inline-flex items-center gap-1.5">
        <span
          className="inline-flex h-2 w-2 rounded-full"
          style={{ backgroundColor: dayTypeDotColor(dayType) }}
        />
        <span>{dayTypeLabel(dayType)}</span>
      </span>
    </Badge>
  );
}

export function MonthDayDrawer({
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
    <Sheet
      open={open}
      onOpenChange={(o) => {
        if (!o) onClose();
      }}
    >
      <SheetContent className="w-full p-0 sm:max-w-lg">
        <div className="h-full bg-[color:var(--app-bg)]">
          {/* Header sticky */}
          <div className="sticky top-0 z-10 border-b border-[color:var(--app-border)] bg-[color:var(--app-surface)]/95 backdrop-blur p-4">
            <SheetHeader className="space-y-2">
              <div className="flex items-start gap-3">
                <div className="min-w-0 flex-1">
                  <SheetTitle>
                    <span className="flex min-w-0 items-center gap-2">
                      <span className="truncate">{dateLabel}</span>
                      {selectedDay ? <DayTypeBadge dayType={selectedDay.day_type} /> : null}
                    </span>
                  </SheetTitle>

                  <SheetDescription className="truncate">
                    Planning du jour
                  </SheetDescription>
                </div>

                <SheetClose asChild>
                  <Button variant="ghost" size="icon" aria-label="Fermer">
                    <X className="h-4 w-4" />
                  </Button>
                </SheetClose>
              </div>
            </SheetHeader>
          </div>

          {/* Content */}
          <div className="space-y-4 p-4">
            {/* Timeline */}
            <div className="rounded-xl border border-[color:var(--app-border)] bg-[color:var(--app-surface)] p-3">
              <div className="text-sm font-semibold text-[color:var(--app-text)]">
                Timeline
              </div>
              <div className="mt-1 text-xs text-[color:var(--app-muted)]">
                Vue synthétique des tranches.
              </div>

              <Separator className="my-3" />

              {selectedDay ? (
                <AgentDayGantt
                  segments={selectedDay.segments}
                  posteNameById={posteNameById}
                  dayStart="00:00:00"
                  dayEnd="23:59:00"
                />
              ) : null}
            </div>

            {/* Tranches */}
            <div className="rounded-xl border border-[color:var(--app-border)] bg-[color:var(--app-surface)] p-3">
              <div className="text-sm font-semibold text-[color:var(--app-text)]">
                Tranches
              </div>
              <div className="mt-1 text-xs text-[color:var(--app-muted)]">
                Détail des affectations par poste.
              </div>

              <Separator className="my-3" />

              {!selectedDay || selectedDay.segments.length === 0 ? (
                <div className="rounded-xl border border-dashed border-[color:var(--app-border)] p-4 text-sm text-[color:var(--app-muted)]">
                  Aucune tranche
                </div>
              ) : (
                <div className="space-y-2">
                  {selectedDay.segments.map((seg) => {
                    const poste = posteNameById.get(seg.posteId) ?? `Poste #${seg.posteId}`;
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
            </div>
          </div>
        </div>
      </SheetContent>
    </Sheet>
  );
}
