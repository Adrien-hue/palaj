export default function Loading() {
  return (
    <div className="space-y-4">
      <div className="h-10 w-48 rounded-lg bg-[color:var(--app-soft)]" />

      <section className="rounded-xl border border-[color:var(--app-border)] bg-[color:var(--app-surface)] p-5">
        <div className="h-7 w-64 rounded-lg bg-[color:var(--app-soft)]" />
        <div className="mt-2 h-4 w-40 rounded-lg bg-[color:var(--app-soft)]" />
      </section>

      <div className="h-[520px] rounded-xl border border-[color:var(--app-border)] bg-[color:var(--app-surface)] p-5">
        <div className="h-full w-full rounded-lg bg-[color:var(--app-soft)]" />
      </div>
    </div>
  );
}
