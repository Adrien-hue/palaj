import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

export type DayType =
  | "working"
  | "rest"
  | "absence"
  | "unknown"
  | "zcot"
  | (string & {});

export function dayTypeLabel(dayType: string) {
  return dayType === "working"
    ? "Travail"
    : dayType === "zcot"
    ? "ZCOT"
    : dayType === "rest"
    ? "Repos"
    : dayType === "absence"
    ? "Absence"
    : dayType === "unknown"
    ? "—"
    : dayType;
}

// shadcn-friendly tokens (no inline styles)
// zcot: close to "working" but distinguishable (teal instead of green)
export function dayTypeDotClass(dayType: string) {
  if (dayType === "working") return "bg-emerald-500";
  if (dayType === "zcot") return "bg-teal-500";
  if (dayType === "absence") return "bg-amber-500";
  if (dayType === "rest") return "bg-muted-foreground/40";
  return "bg-muted-foreground/40";
}

export function DayTypeBadge({ dayType, className }: { dayType: DayType; className?: string }) {
  return (
    <Badge
      variant="outline"
      className={cn("shrink-0 rounded-full px-2 py-0.5 text-[11px] font-medium", className)}
    >
      <span className="inline-flex items-center gap-1.5">
        <span className={cn("inline-flex h-2 w-2 rounded-full", dayTypeDotClass(dayType))} />
        <span>{dayTypeLabel(dayType)}</span>
      </span>
    </Badge>
  );
}
