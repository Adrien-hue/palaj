"use client";

import { Badge } from "@/components/ui/badge";

export function AdminStatBadge({ active }: { active: boolean }) {
  return (
    <Badge variant="secondary" className="gap-2">
      <span
        className={[
          "inline-flex h-2 w-2 rounded-full",
          active
            ? "bg-emerald-500 dark:bg-emerald-400"
            : "bg-rose-500 dark:bg-rose-400",
        ].join(" ")}
        aria-hidden="true"
      />
      <span>{active ? "Actif" : "Inactif"}</span>
    </Badge>
  );
}
