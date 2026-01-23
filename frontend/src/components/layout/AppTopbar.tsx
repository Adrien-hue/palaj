"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { ArrowUpRight } from "lucide-react";

import { APP_TOP_NAV, AppNavItem } from "@/navigation/appNav";
import { PalajBrand } from "@/components/layout/PalajBrand";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  NavigationMenu,
  NavigationMenuItem,
  NavigationMenuLink,
  NavigationMenuList,
} from "@/components/ui/navigation-menu";

function isNavActive(pathname: string, item: AppNavItem) {
  if (item.isActive) return item.isActive(pathname);
  return pathname === item.href || pathname.startsWith(item.href + "/");
}

function TopNav() {
  const pathname = usePathname();

  return (
    <NavigationMenu>
      <NavigationMenuList className="gap-1">
        {APP_TOP_NAV.map((item) => {
          const active = isNavActive(pathname, item);

          return (
            <NavigationMenuItem key={item.href}>
              <NavigationMenuLink asChild>
                <Link
                  href={item.href}
                  className={[
                    "rounded-md px-3 py-2 text-sm font-medium transition",
                    "focus:outline-none focus-visible:ring-2 focus-visible:ring-[color:var(--app-focus)]",
                    active
                      ? "bg-[color:var(--app-surface)] text-[color:var(--app-text)] shadow-sm ring-1 ring-[color:var(--app-border)]"
                      : "text-[color:var(--app-muted)] hover:bg-[color:var(--app-surface)] hover:text-[color:var(--app-text)]",
                  ].join(" ")}
                  aria-current={active ? "page" : undefined}
                >
                  {item.label}
                </Link>
              </NavigationMenuLink>
            </NavigationMenuItem>
          );
        })}
      </NavigationMenuList>
    </NavigationMenu>
  );
}

export function AppTopbar() {
  const pathname = usePathname();

  return (
    <header className="sticky top-0 z-50 border-b border-[color:var(--app-topbar-border)] bg-[color:var(--app-topbar-bg)] backdrop-blur">
      <div className="mx-auto flex h-14 w-full max-w-[1600px] items-center justify-between px-6">
        <div className="flex items-center gap-4">
          <PalajBrand />
          <TopNav />
        </div>

        <div className="flex items-center gap-2">
          {/* Placeholder search (plus tard) */}
          <div className="hidden md:block">
            <Input
              readOnly
              value="Rechercher…"
              aria-label="Rechercher (bientôt disponible)"
              className={[
                "h-9 w-56 cursor-default",
                "border-[color:var(--app-border)] bg-[color:var(--app-surface)] text-[color:var(--app-muted)]",
                "focus-visible:ring-0 focus-visible:ring-offset-0",
              ].join(" ")}
            />
          </div>

          <Button asChild variant="ghost" className="text-[color:var(--app-muted)] hover:text-[color:var(--app-text)]">
            <Link href="/admin">
              Admin <ArrowUpRight className="ml-2 h-4 w-4" />
            </Link>
          </Button>
        </div>
      </div>
    </header>
  );
}