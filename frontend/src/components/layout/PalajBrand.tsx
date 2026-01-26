import Link from "next/link";
import { cn } from "@/lib/utils";

export function PalajBrand({
  href = "/app",
  collapsed = false,
  className,
}: {
  href?: string;
  collapsed?: boolean;
  className?: string;
}) {
  return (
    <Link
      href={href}
      className={cn(
        "flex items-center gap-3 rounded-md px-2 py-1 transition-colors hover:bg-muted",
        className
      )}
      aria-label="PALAJ"
    >
      <div
        className="h-9 w-9 rounded-xl ring-1 ring-border"
        style={{
          background:
            "linear-gradient(135deg, var(--palaj-l) 20%, var(--palaj-a) 50%, var(--palaj-j) 80%)",
        }}
      />

      {!collapsed && (
        <div className="flex flex-col leading-tight">
          <span className="text-sm font-semibold text-foreground">PALAJ</span>

          <span className="text-[11px] tracking-wide">
            <span style={{ color: "var(--palaj-l)" }} className="font-semibold">
              L
            </span>
            <span className="px-1 text-muted-foreground">•</span>
            <span style={{ color: "var(--palaj-a)" }} className="font-semibold">
              A
            </span>
            <span className="px-1 text-muted-foreground">•</span>
            <span style={{ color: "var(--palaj-j)" }} className="font-semibold">
              J
            </span>
          </span>
        </div>
      )}
    </Link>
  );
}
