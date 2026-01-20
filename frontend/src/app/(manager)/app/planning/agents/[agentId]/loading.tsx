export default function Loading() {
  return (
    <div className="space-y-4">
      {/* Header fused card */}
      <section className="rounded-xl border border-[color:var(--app-border)] bg-[color:var(--app-surface)] p-5 shadow-sm space-y-4">
        <div className="h-4 w-80 rounded-lg bg-[color:var(--app-soft)]" />
        <div className="flex items-start justify-between gap-4">
          <div>
            <div className="h-7 w-64 rounded-lg bg-[color:var(--app-soft)]" />
            <div className="mt-2 h-4 w-40 rounded-lg bg-[color:var(--app-soft)]" />
          </div>
          <div className="h-10 w-28 rounded-xl bg-[color:var(--app-soft)]" />
        </div>

        <div className="h-10 w-full rounded-xl bg-[color:var(--app-soft)]" />
      </section>

      {/* Grid skeleton */}
      <div className="h-[520px] rounded-xl border border-[color:var(--app-border)] bg-[color:var(--app-surface)] p-5">
        <div className="h-full w-full rounded-lg bg-[color:var(--app-soft)]" />
      </div>
    </div>
  );
}
