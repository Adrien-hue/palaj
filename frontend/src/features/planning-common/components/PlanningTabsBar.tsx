"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { PLANNING_TABS } from "@/navigation/appNav";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";

function isActive(pathname: string, href: string) {
  return pathname === href || pathname.startsWith(href + "/");
}

export function PlanningTabsBar() {
  const pathname = usePathname();

  const active = PLANNING_TABS.find((t) => isActive(pathname, t.href))?.href ?? PLANNING_TABS[0]?.href;

  return (
    <div className="border-b border-[color:var(--app-border)] bg-[color:var(--app-topbar-bg)]/60 backdrop-blur">
      <div className="mx-auto w-full max-w-[1600px] px-6 py-2">
        <Tabs value={active}>
          <TabsList className="bg-[color:var(--app-surface)]">
            {PLANNING_TABS.map((t) => (
              <TabsTrigger key={t.href} value={t.href} asChild>
                <Link href={t.href}>{t.label}</Link>
              </TabsTrigger>
            ))}
          </TabsList>
        </Tabs>
      </div>
    </div>
  );
}
