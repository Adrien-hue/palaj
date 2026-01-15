"use client";

export function AdminDetailsCard({
  title,
  right,
  children,
}: {
  title: string;
  right?: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <div className="rounded-2xl bg-white p-4 ring-1 ring-zinc-200">
      <div className="flex items-center justify-between gap-4">
        <div className="text-sm font-semibold text-zinc-900">{title}</div>
        {right ? <div className="shrink-0">{right}</div> : null}
      </div>
      <div className="mt-3">{children}</div>
    </div>
  );
}
