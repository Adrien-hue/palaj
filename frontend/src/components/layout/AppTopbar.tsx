// src/components/layout/AppTopbar.tsx
"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { APP_TOP_NAV, PLANNING_TABS } from "@/navigation/appNav";

function isActive(pathname: string, href: string) {
  if (href === "/") return pathname === "/";
  return pathname === href || pathname.startsWith(href + "/");
}

function TopNav() {
  const pathname = usePathname();

  return (
    <nav className="flex items-center gap-1">
      {APP_TOP_NAV.map((item) => {
        const active = isActive(pathname, item.href);
        return (
          <Link
            key={item.href}
            href={item.href}
            className={[
              "rounded-md px-3 py-2 text-sm font-medium transition-colors",
              active
                ? "bg-zinc-900 text-white"
                : "text-zinc-700 hover:bg-zinc-100",
            ].join(" ")}
          >
            {item.label}
          </Link>
        );
      })}
    </nav>
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
                "rounded-md px-3 py-2 text-sm transition-colors",
                active
                  ? "bg-white text-zinc-950 shadow-sm ring-1 ring-zinc-200"
                  : "text-zinc-700 hover:bg-white hover:ring-1 hover:ring-zinc-200",
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
  return (
    <header className="sticky top-0 z-50 border-b border-zinc-200 bg-zinc-50/80 backdrop-blur">
      <div className="mx-auto flex h-14 w-full max-w-[1600px] items-center justify-between px-6">
        <div className="flex items-center gap-4">
          <Link href="/app" className="text-sm font-semibold text-zinc-950">
            PALAJ
          </Link>
          <TopNav />
        </div>

        <div className="flex items-center gap-2">
          {/* placeholder search/action */}
          <div className="hidden md:block">
            <div className="rounded-md border border-zinc-200 bg-white px-3 py-2 text-sm text-zinc-500">
              Rechercher… (bientôt)
            </div>
          </div>

          <Link
            href="/admin"
            className="rounded-md px-3 py-2 text-sm text-zinc-700 hover:bg-zinc-100"
          >
            Admin
          </Link>
        </div>
      </div>

      <PlanningTabs />
    </header>
  );
}
