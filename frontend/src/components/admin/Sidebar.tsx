"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Users, Briefcase, BadgeCheck, ChevronLeft } from "lucide-react";

const nav = [
  { label: "Agents", href: "/admin/agents", icon: Users },
  { label: "Postes", href: "/admin/postes", icon: Briefcase },
  { label: "Régimes", href: "/admin/regimes", icon: BadgeCheck },
] as const;

function cn(...classes: Array<string | false | undefined>) {
  return classes.filter(Boolean).join(" ");
}

export default function Sidebar({
  collapsed,
  setCollapsed,
}: {
  collapsed: boolean;
  setCollapsed: (collapsed: boolean) => void;
}) {
  const pathname = usePathname();

  return (
    <aside
      className={cn(
        "shrink-0 border-r border-zinc-200 bg-white transition-[width] duration-200",
        collapsed ? "w-16" : "w-64"
      )}
    >
      {/* Header */}
      <div className="border-b border-zinc-100 p-2">
        {collapsed ? (
          // Collapsed: layout vertical (logo puis bouton)
          <div className="flex flex-col items-center gap-2">
            <div
              className="h-9 w-9 rounded-xl ring-1 ring-zinc-200"
              style={{
                background:
                  "linear-gradient(135deg, var(--palaj-l) 20%, var(--palaj-a) 50%, var(--palaj-j) 80%)",
              }}
            />
            <button
              className="rounded-lg p-2 hover:bg-zinc-100"
              onClick={() => setCollapsed(false)}
              aria-label="Expand sidebar"
            >
              <ChevronLeft className="h-5 w-5 rotate-180" />
            </button>
          </div>
        ) : (
          // Expanded: layout horizontal
          <div className="flex h-14 items-center justify-between">
            <div className="flex items-center gap-2 overflow-hidden">
              <div
                className="h-9 w-9 shrink-0 rounded-xl ring-1 ring-zinc-200"
                style={{
                  background:
                    "linear-gradient(135deg, var(--palaj-l) 20%, var(--palaj-a) 50%, var(--palaj-j) 80%)",
                }}
              />
              <div className="min-w-0 leading-tight">
                <div className="truncate text-sm font-semibold">PALAJ</div>
                <div className="truncate text-xs text-zinc-500">Admin</div>
              </div>
            </div>

            <button
              className="shrink-0 rounded-lg p-2 hover:bg-zinc-100"
              onClick={() => setCollapsed(true)}
              aria-label="Collapse sidebar"
            >
              <ChevronLeft className="h-5 w-5 transition-transform" />
            </button>
          </div>
        )}
      </div>

      {/* Nav */}
      <nav className="px-2 py-3">
        {nav.map((item) => {
          const active =
            pathname === item.href || pathname.startsWith(item.href + "/");
          const Icon = item.icon;

          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "group flex items-center gap-3 rounded-xl px-3 py-2 text-sm transition",
                active
                  ? "bg-zinc-900 text-white"
                  : "text-zinc-700 hover:bg-zinc-100"
              )}
              title={collapsed ? item.label : undefined}
            >
              <Icon
                className={cn(
                  "h-5 w-5",
                  active ? "text-white" : "text-zinc-500"
                )}
              />
              {!collapsed && <span className="font-medium">{item.label}</span>}
            </Link>
          );
        })}
      </nav>

      {/* Footer hint */}
      {!collapsed && (
        <div className="mt-auto p-4">
          <div className="flex items-center gap-2 text-xs text-zinc-500">
            <span
              className="inline-flex h-2 w-2 rounded-full"
              style={{ backgroundColor: "var(--palaj-l)" }}
            />
            <span
              className="inline-flex h-2 w-2 rounded-full"
              style={{ backgroundColor: "var(--palaj-a)" }}
            />
            <span
              className="inline-flex h-2 w-2 rounded-full ring-1 ring-zinc-200"
              style={{ backgroundColor: "var(--palaj-j)" }}
            />
            <span>L • A • J</span>
          </div>
        </div>
      )}
    </aside>
  );
}
