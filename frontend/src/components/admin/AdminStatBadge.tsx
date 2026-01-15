"use client";

export function AdminStatBadge({ active }: { active: boolean }) {
  return (
    <span
      className={[
        "inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium",
        active ? "bg-green-100 text-green-700" : "bg-red-100 text-red-700",
      ].join(" ")}
    >
      {active ? "Actif" : "Inactif"}
    </span>
  );
}
