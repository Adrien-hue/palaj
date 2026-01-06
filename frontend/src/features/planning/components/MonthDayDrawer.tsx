"use client";

import { useEffect } from "react";

import { Button } from "@/components/ui";
import { formatDateFR } from "@/utils/date.format";

import type { AgentDayVm } from "@/features/planning/vm/planning.vm";
import { DayGantt } from "./DayGantt";

function DayTypeBadge({ dayType }: { dayType: string }) {
  const label =
    dayType === "working"
      ? "Travail"
      : dayType === "rest"
      ? "Repos"
      : dayType === "absence"
      ? "Absence"
      : dayType === "unknown"
      ? "—"
      : dayType;

  const cls =
    dayType === "working"
      ? "bg-emerald-50 text-emerald-700 border-emerald-200"
      : dayType === "rest"
      ? "bg-slate-50 text-slate-700 border-slate-200"
      : dayType === "absence"
      ? "bg-rose-50 text-rose-700 border-rose-200"
      : "bg-muted text-muted-foreground border-border";

  return (
    <span
      className={`inline-flex items-center rounded-full border px-2 py-0.5 text-[11px] font-medium ${cls}`}
    >
      {label}
    </span>
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
  useEffect(() => {
    if (!open) return;

    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };

    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [open, onClose]);

  if (!open || !selectedDay) return null;

  const dateLabel = formatDateFR(selectedDay.day_date);

  return (
    <div className="fixed inset-0 z-50">
      <div className="absolute inset-0 bg-black/30" onClick={onClose} />

      <aside className="absolute right-0 top-0 h-full w-full max-w-lg bg-background shadow-2xl">
        {/* Header */}
        <div className="flex items-start justify-between gap-3 border-b border-border p-5">
          <div className="min-w-0">
            <div className="text-lg font-semibold text-foreground">
              {dateLabel}
            </div>

            <div className="mt-1 flex flex-wrap items-center gap-2">
              <DayTypeBadge dayType={selectedDay.day_type} />
              <span className="text-sm text-muted-foreground">
                Planning du jour
              </span>
            </div>
          </div>

          <Button variant="dangerSoft" onClick={onClose} title="Fermer (Échap)">
            Fermer
          </Button>
        </div>

        {/* Content */}
        <div className="space-y-4 p-5">
          {/* Timeline */}
          <div className="rounded-2xl border border-border bg-card p-4">
            <div className="mb-3 text-sm font-semibold text-foreground">
              Timeline
            </div>
            <DayGantt
              segments={selectedDay.segments}
              posteNameById={posteNameById}
              dayStart="00:00:00"
              dayEnd="23:59:00"
            />
          </div>

          {/* Tranches */}
          <div className="rounded-2xl border border-border bg-card p-4">
            <div className="mb-3 text-sm font-semibold text-foreground">
              Tranches
            </div>

            {selectedDay.segments.length === 0 ? (
              <div className="rounded-xl border border-dashed border-border p-3 text-sm text-muted-foreground">
                Aucune tranche
              </div>
            ) : (
              <div className="space-y-2">
                {selectedDay.segments.map((seg) => {
                  const poste =
                    posteNameById.get(seg.posteId) ?? `Poste #${seg.posteId}`;

                  return (
                    <div
                      key={seg.key}
                      className="rounded-xl border border-border bg-background px-3 py-2"
                    >
                      <div className="flex items-center justify-between gap-3">
                        <div className="min-w-0">
                          <div className="truncate text-sm font-semibold text-foreground">
                            {seg.nom}
                            {seg.continuesPrev ? " ←" : ""}
                            {seg.continuesNext ? " →" : ""}
                          </div>
                          <div className="truncate text-xs text-muted-foreground">
                            {poste}
                          </div>
                        </div>

                        <div className="shrink-0 text-right text-xs font-medium tabular-nums text-muted-foreground">
                          {seg.start.slice(0, 5)}–{seg.end.slice(0, 5)}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      </aside>
    </div>
  );
}
