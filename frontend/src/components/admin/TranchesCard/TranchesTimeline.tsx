"use client";

import { useCallback, useMemo, useState } from "react";
import type { TimelineTooltipState, TranchesTimelineProps } from "./types";
import { formatHHMM, trancheToSegments } from "./helpers";

const TOTAL_MINUTES = 1440;
const LANES = 4;
const LANE_HEIGHT = 16;
const TOOLTIP_OFFSET = 12;

export default function TranchesTimeline({
  tranches,
  markerEveryHours = 3,
  onSelectTranche,
}: TranchesTimelineProps) {
  const trackHeight = LANES * LANE_HEIGHT;

  const markers = useMemo(() => {
    const res: number[] = [];
    for (let h = 0; h <= 24; h += markerEveryHours) res.push(h);
    return res;
  }, [markerEveryHours]);

  const [tooltip, setTooltip] = useState<TimelineTooltipState>(null);
  const [hoveredId, setHoveredId] = useState<number | null>(null);

  const hideTooltip = useCallback(() => setTooltip(null), []);

  const showTooltip = useCallback((e: React.MouseEvent, text: string) => {
    // Fixed positioning so it never gets clipped by parent overflow.
    setTooltip({
      text,
      x: e.clientX + TOOLTIP_OFFSET,
      y: e.clientY - TOOLTIP_OFFSET,
    });
  }, []);

  const moveTooltip = useCallback((e: React.MouseEvent) => {
    setTooltip((prev) =>
      prev
        ? { ...prev, x: e.clientX + TOOLTIP_OFFSET, y: e.clientY - TOOLTIP_OFFSET }
        : prev
    );
  }, []);

  return (
    <div className="mt-3 rounded-xl bg-zinc-50 p-3 ring-1 ring-zinc-200">
      <div className="text-sm font-semibold text-zinc-900">Timeline (24h)</div>
      <div className="mt-1 text-xs text-zinc-600">
        Survolez une tranche pour voir les heures exactes.
      </div>

      {tooltip ? (
        <div
          className="pointer-events-none fixed z-[9999] max-w-[260px] rounded-lg bg-zinc-900 px-2 py-1 text-[11px] text-white shadow-lg"
          style={{ left: tooltip.x, top: tooltip.y }}
        >
          {tooltip.text}
        </div>
      ) : null}

      <div className="mt-3">
        <div className="relative h-6">
          {markers.map((h) => {
            const leftPct = (h * 60 * 100) / TOTAL_MINUTES;
            const label = `${String(h).padStart(2, "0")}:00`;

            return (
              <div key={h} className="absolute top-0" style={{ left: `${leftPct}%` }}>
                <div className="-translate-x-1/2 text-[10px] font-medium text-zinc-600">
                  {label}
                </div>
              </div>
            );
          })}
        </div>

        <div
          className="relative w-full overflow-hidden rounded-lg bg-white ring-1 ring-zinc-200"
          style={{ height: `${trackHeight}px` }}
          onMouseLeave={() => {
            setHoveredId(null);
            hideTooltip();
          }}
        >
          {markers.map((h) => {
            const leftPct = (h * 60 * 100) / TOTAL_MINUTES;
            return (
              <div
                key={`grid-${h}`}
                className="absolute top-0 h-full w-px bg-zinc-200"
                style={{ left: `${leftPct}%` }}
              />
            );
          })}

          {/* Bars */}
          {tranches.flatMap((t, idx) => {
            const lane = idx % LANES;
            const top = lane * LANE_HEIGHT + 2;

            const segments = trancheToSegments(t.heure_debut, t.heure_fin);
            const tooltipText = `${t.nom} — ${formatHHMM(t.heure_debut)} → ${formatHHMM(
              t.heure_fin
            )}`;

            const isHovered = hoveredId === t.id;
            const isDimmed = hoveredId !== null && hoveredId !== t.id;

            return segments.map((seg, segIdx) => {
              const leftPct = (seg.startMin * 100) / TOTAL_MINUTES;
              const widthPct = ((seg.endMin - seg.startMin) * 100) / TOTAL_MINUTES;

              return (
                <div
                  key={`${t.id}-${segIdx}`}
                  className={["absolute cursor-pointer", isHovered ? "z-20" : "z-10"].join(
                    " "
                  )}
                  style={{
                    top: `${top}px`,
                    left: `${leftPct}%`,
                    width: `${widthPct}%`,
                  }}
                  onClick={() => onSelectTranche?.(t.id)}
                  onMouseEnter={(e) => {
                    setHoveredId(t.id);
                    showTooltip(e, tooltipText);
                  }}
                  onMouseMove={moveTooltip}
                  onMouseLeave={() => {
                    setHoveredId((cur) => (cur === t.id ? null : cur));
                    hideTooltip();
                  }}
                  title={tooltipText}
                >
                  <div
                    className={[
                      "h-3 rounded-md px-1 text-[10px] font-medium text-white shadow-sm ring-1 transition",
                      "bg-zinc-900/80 ring-zinc-900/10",
                      isHovered ? "bg-zinc-900 ring-2 ring-zinc-400 shadow-md scale-[1.03]" : "",
                      isDimmed ? "opacity-40" : "opacity-100",
                    ].join(" ")}
                  >
                    <div className="truncate leading-3">{t.nom}</div>
                  </div>
                </div>
              );
            });
          })}
        </div>
      </div>
    </div>
  );
}
