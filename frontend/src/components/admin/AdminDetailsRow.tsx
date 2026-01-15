"use client";

export function AdminDetailsRow({
  label,
  value,
}: {
  label: string;
  value: React.ReactNode;
}) {
  return (
    <div className="flex items-start justify-between gap-4 py-2">
      <div className="text-xs font-medium text-zinc-600">{label}</div>
      <div className="text-sm text-zinc-900 text-right">{value}</div>
    </div>
  );
}
