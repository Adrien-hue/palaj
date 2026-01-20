"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { ArrowUpRight } from "lucide-react";
import { APP_TOP_NAV, PLANNING_TABS } from "@/navigation/appNav";
import { PalajBrand } from "@/components/layout/PalajBrand";

function isActive(pathname: string, href: string) {
  return pathname === href || pathname.startsWith(href + "/");
}

function NavLink({
  href,
  label,
  active,
}: {
  href: string;
  label: string;
  active: boolean;
}) {
  return (
    <Link
      href={href}
      className={[
        "rounded-md px-3 py-2 text-sm font-medium transition",
        active
          ? "bg-[color:var(--app-surface)] text-[color:var(--app-text)] shadow-sm ring-1 ring-[color:var(--app-border)]"
          : "text-[color:var(--app-muted)] hover:bg-[color:var(--app-surface)] hover:text-[color:var(--app-text)]",
      ].join(" ")}
    >
      {label}
    </Link>
  );
}

function PlanningTabs() {
  const pathname = usePathname();
  const inPlanning = pathname.startsWith("/app/planning");
  if (!inPlanning) return null;

  return (
    <div className="mx-auto w-full max-w-[1600px] px-6 pb-3">
      <div className="flex items-center gap-1">
        {PLANNING_TABS.map((tab) => {
          const active = isActive(pathname, tab.href);
          return (
            <Link
              key={tab.href}
              href={tab.href}
              className={[
                "rounded-md px-3 py-2 text-sm transition",
                active
                  ? "bg-[color:var(--app-surface)] text-[color:var(--app-text)] shadow-sm ring-1 ring-[color:var(--app-border)]"
                  : "text-[color:var(--app-muted)] hover:bg-[color:var(--app-surface)] hover:text-[color:var(--app-text)]",
              ].join(" ")}
            >
              {tab.label}
            </Link>
          );
        })}
      </div>
    </div>
  );
}

export function AppTopbar() {
  const pathname = usePathname();

  return (
    <header className="sticky top-0 z-50 border-b border-[color:var(--app-topbar-border)] bg-[color:var(--app-topbar-bg)] backdrop-blur">
      <div className="mx-auto flex h-14 w-full max-w-[1600px] items-center justify-between px-6">
        <div className="flex items-center gap-4">
          
          <PalajBrand />

          <nav className="flex items-center gap-1">
            {APP_TOP_NAV.map((item) => (
              <NavLink
                key={item.href}
                href={item.href}
                label={item.label}
                active={isActive(pathname, item.href)}
              />
            ))}
          </nav>
        </div>

        <div className="flex items-center gap-2">
          {/* Placeholder search (plus tard) */}
          <div className="hidden md:flex items-center gap-2 rounded-md border border-[color:var(--app-border)] bg-[color:var(--app-surface)] px-3 py-2 text-sm text-[color:var(--app-muted)]">
            Rechercher…
          </div>

          <Link
            href="/admin"
            className="inline-flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium text-[color:var(--app-muted)] transition hover:bg-[color:var(--app-surface)] hover:text-[color:var(--app-text)]"
          >
            Admin
            <ArrowUpRight className="h-4 w-4" />
          </Link>
        </div>
      </div>

      <PlanningTabs />
    </header>
  );
}
