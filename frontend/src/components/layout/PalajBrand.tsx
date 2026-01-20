import Link from "next/link";

export function PalajBrand() {
  return (
    <Link
      href="/app"
      className="flex items-center gap-3 rounded-md px-2 py-1 transition hover:bg-[color:var(--app-surface)]"
    >
      <div
        className="h-9 w-9 rounded-xl ring-1 ring-[color:var(--app-border)]"
        style={{
          background:
            "linear-gradient(135deg, var(--palaj-l) 20%, var(--palaj-a) 50%, var(--palaj-j) 80%)",
        }}
      />

      <div className="flex flex-col leading-tight">
        <span className="text-sm font-semibold text-[color:var(--app-text)]">
          PALAJ
        </span>

        <span className="text-[11px] tracking-wide">
          <span style={{ color: "var(--palaj-l)" }} className="font-semibold">
            L
          </span>
          <span className="px-1 text-[color:var(--app-muted)]">•</span>
          <span style={{ color: "var(--palaj-a)" }} className="font-semibold">
            A
          </span>
          <span className="px-1 text-[color:var(--app-muted)]">•</span>
          <span style={{ color: "var(--palaj-j)" }} className="font-semibold">
            J
          </span>
        </span>
      </div>
    </Link>
  );
}
