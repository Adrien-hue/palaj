import type { AgentDayVm } from "../vm/agentPlanning.vm";
import type { RhViolation } from "@/types/rhValidation";
import { Badge } from "@/components/ui/badge";
import { DayTypeBadge, dayTypeLabel } from "@/components/planning/DayTypeBadge";
import { formatDateFRLong } from "@/utils/date.format";

function severityLabel(s: RhViolation["severity"]) {
  if (s === "error") return "Erreur RH";
  if (s === "warning") return "Alerte RH";
  return "Info RH";
}

function severityBadgeVariant(s: RhViolation["severity"]): React.ComponentProps<typeof Badge>["variant"] {
  if (s === "error") return "destructive";
  if (s === "warning") return "secondary";
  return "outline";
}

export function AgentDayCellTooltip({
  day,
  windows,
  effectiveDayType,
  rhViolations,
}: {
  day: AgentDayVm;
  windows: { start: string; end: string }[];
  effectiveDayType: AgentDayVm["day_type"] | "zcot";
  rhViolations: RhViolation[];
}) {
  const dateISO = day.day_date.slice(0, 10);
  const dateLabel = typeof formatDateFRLong === "function" ? formatDateFRLong(dateISO) : dateISO;

  const hasWindows = windows.length > 0;

  const rhSorted = rhViolations
    .slice()
    .sort((a, b) => {
      const rank = (s: RhViolation["severity"]) => (s === "error" ? 0 : s === "warning" ? 1 : 2);
      return rank(a.severity) - rank(b.severity);
    });

  const rhErrors = rhSorted.filter((v) => v.severity === "error");
  const rhWarnings = rhSorted.filter((v) => v.severity === "warning");
  const rhInfos = rhSorted.filter((v) => v.severity === "info");

  return (
    <div className="space-y-2">
      {/* Header */}
      <div className="flex items-center justify-between gap-2">
        <div className="text-xs font-medium">{dateLabel}</div>
        <div className="flex items-center gap-2">
          <DayTypeBadge dayType={effectiveDayType as any} />
        </div>
      </div>

      {/* Optional day description (if you have one) */}
      {day.description ? (
        <div className="text-xs text-muted-foreground line-clamp-2">{day.description}</div>
      ) : null}

      {/* Hours */}
      {!hasWindows ? (
        <div className="text-xs text-muted-foreground">{dayTypeLabel(effectiveDayType as any)}</div>
      ) : (
        <div className="space-y-1">
          <div className="text-xs font-medium">Horaires</div>
          {windows.slice(0, 4).map((w, i) => (
            <div
              key={i}
              className="flex items-center justify-between gap-2 text-xs tabular-nums text-muted-foreground"
            >
              <span>
                {w.start.slice(0, 5)} – {w.end.slice(0, 5)}
              </span>
            </div>
          ))}
          {windows.length > 4 ? (
            <div className="text-[11px] text-muted-foreground">+{windows.length - 4} plage(s)</div>
          ) : null}
        </div>
      )}

      {/* RH violations */}
      {rhSorted.length > 0 ? (
        <div className="space-y-1 pt-1">
          <div className="text-xs font-medium">Contrôle RH</div>

          {rhErrors.length > 0 ? (
            <div className="space-y-1">
              {rhErrors.slice(0, 3).map((v, i) => (
                <div key={`e-${v.code}-${i}`} className="flex items-start gap-2">
                  <Badge variant={severityBadgeVariant(v.severity)} className="h-5 rounded-full px-2 py-0 text-[10px]">
                    {severityLabel(v.severity)}
                  </Badge>
                  <div className="min-w-0 text-xs text-muted-foreground">{v.message}</div>
                </div>
              ))}
              {rhErrors.length > 3 ? (
                <div className="text-[11px] text-muted-foreground">+{rhErrors.length - 3} erreur(s)</div>
              ) : null}
            </div>
          ) : null}

          {rhWarnings.length > 0 ? (
            <div className="space-y-1">
              {rhWarnings.slice(0, 2).map((v, i) => (
                <div key={`w-${v.code}-${i}`} className="flex items-start gap-2">
                  <Badge variant={severityBadgeVariant(v.severity)} className="h-5 rounded-full px-2 py-0 text-[10px]">
                    {severityLabel(v.severity)}
                  </Badge>
                  <div className="min-w-0 text-xs text-muted-foreground">{v.message}</div>
                </div>
              ))}
              {rhWarnings.length > 2 ? (
                <div className="text-[11px] text-muted-foreground">+{rhWarnings.length - 2} alerte(s)</div>
              ) : null}
            </div>
          ) : null}

          {rhInfos.length > 0 ? (
            <div className="text-[11px] text-muted-foreground">
              {rhInfos.length} info(s) RH
            </div>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}
