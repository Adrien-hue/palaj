"use client";

import { useEffect } from "react";
import { X } from "lucide-react";

import { formatDateFR } from "@/utils/date.format";
import type { AgentDayVm } from "@/features/planning/vm/planning.vm";
import { DayGantt } from "./DayGantt";

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
  const label = dayTypeLabel(dayType);

  return (
    <span className="inline-flex items-center gap-1.5 rounded-full border border-[color:var(--app-border)] bg-[color:var(--app-surface)] px-2 py-0.5 text-[11px] font-medium">
      <span
        className="inline-flex h-2 w-2 rounded-full"
        style={{ backgroundColor: dayTypeDotColor(dayType) }}
      />
      <span className="text-[color:var(--app-text)]">{label}</span>
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
  const titleId = "palaj-day-drawer-title";

  return (
    <div className="fixed inset-0 z-50">
      {/* Overlay */}
      <div
        className="absolute inset-0 bg-black/30"
        onClick={onClose}
        aria-hidden="true"
      />

      <aside
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        className="absolute right-0 top-0 h-full w-full max-w-lg border-l border-[color:var(--app-border)] bg-[color:var(--app-bg)] shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-start justify-between gap-3 border-b border-[color:var(--app-border)] p-5">
          <div className="min-w-0">
            <div
              id={titleId}
              className="text-lg font-semibold text-[color:var(--app-text)]"
            >
              {dateLabel}
            </div>

            <div className="mt-1 flex flex-wrap items-center gap-2">
              <DayTypeBadge dayType={selectedDay.day_type} />
              <span className="text-sm text-[color:var(--app-muted)]">
                Planning du jour
              </span>
            </div>
          </div>

          <button
            type="button"
            onClick={onClose}
            title="Fermer (Échap)"
            className="inline-flex items-center gap-2 rounded-xl border border-[color:var(--app-border)] bg-[color:var(--app-surface)] px-3 py-2 text-sm font-medium text-[color:var(--app-text)] transition hover:bg-[color:var(--app-soft)] hover:ring-1 hover:ring-[color:var(--app-ring)] hover:ring-inset focus:outline-none focus-visible:ring-2 focus-visible:ring-zinc-900/10"
          >
            <X className="h-4 w-4" />
            Fermer
          </button>
        </div>

        {/* Content */}
        <div className="space-y-4 p-5">
          {/* Timeline */}
          <section className="rounded-xl border border-[color:var(--app-border)] bg-[color:var(--app-surface)] p-4">
            <div className="mb-3 text-sm font-semibold text-[color:var(--app-text)]">
              Timeline
            </div>
            <DayGantt
              segments={selectedDay.segments}
              posteNameById={posteNameById}
              dayStart="00:00:00"
              dayEnd="23:59:00"
            />
          </section>

          {/* Tranches */}
          <section className="rounded-xl border border-[color:var(--app-border)] bg-[color:var(--app-surface)] p-4">
            <div className="mb-3 text-sm font-semibold text-[color:var(--app-text)]">
              Tranches
            </div>

            {selectedDay.segments.length === 0 ? (
              <div className="rounded-xl border border-dashed border-[color:var(--app-border)] p-3 text-sm text-[color:var(--app-muted)]">
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
                      className="rounded-xl border border-[color:var(--app-border)] bg-[color:var(--app-bg)] px-3 py-2"
                    >
                      <div className="flex items-center justify-between gap-3">
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

                        <div className="shrink-0 text-right text-xs font-medium tabular-nums text-[color:var(--app-muted)]">
                          {seg.start.slice(0, 5)}–{seg.end.slice(0, 5)}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </section>
        </div>
      </aside>
    </div>
  );
}
