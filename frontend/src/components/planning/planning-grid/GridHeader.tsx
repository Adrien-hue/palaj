import { cn } from "@/lib/utils";
import type { DayHeaderLabel } from "./types";

export function GridHeader({
  days,
  className,
}: {
  days: DayHeaderLabel[];
  className?: string;
}) {
  return (
    <div
      className={cn(
        "sticky top-0 z-10 border-b bg-card/95 backdrop-blur supports-[backdrop-filter]:bg-card/75",
        className
      )}
    >
      <div className="grid grid-cols-7 gap-2 px-2 py-2 sm:gap-3" role="row">
        {days.map((d) => {
          const weekend = d.short === "Sam" || d.short === "Dim";
          return (
            <div
              key={d.short}
              role="columnheader"
              className={cn(
                "px-1.5 text-xs font-medium tracking-tight sm:px-2 sm:text-sm",
                weekend ? "text-foreground" : "text-muted-foreground"
              )}
            >
              <span className="hidden sm:inline">{d.full}</span>
              <span className="sm:hidden">{d.short}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
