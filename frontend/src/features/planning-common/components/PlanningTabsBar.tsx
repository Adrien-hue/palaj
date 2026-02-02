"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { PLANNING_TABS } from "@/navigation/appNav";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { cn } from "@/lib/utils";

function isActive(pathname: string, href: string) {
  return pathname === href || pathname.startsWith(href + "/");
}

export function PlanningTabsBar() {
  const pathname = usePathname();

  const active =
    PLANNING_TABS.find((t) => isActive(pathname, t.href))?.href ??
    PLANNING_TABS[0]?.href;

  return (
    <div className="border-b bg-background/80 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="mx-auto w-full max-w-[1600px] px-6 py-2">
        <Tabs value={active}>
          <TabsList
            className={cn(
              "bg-muted p-1",
              "text-muted-foreground"
            )}
          >
            {PLANNING_TABS.map((t) => (
              <TabsTrigger
                key={t.href}
                value={t.href}
                asChild
                className={cn(
                  "px-3 py-1.5 text-sm font-medium",
                  "transition-colors",
                  "data-[state=active]:bg-background data-[state=active]:text-foreground",
                  "data-[state=active]:shadow-sm",
                )}
              >
                <Link href={t.href}>{t.label}</Link>
              </TabsTrigger>
            ))}
          </TabsList>
        </Tabs>
      </div>
    </div>
  );
}
