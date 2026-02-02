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
import { cn } from "@/lib/utils";

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
                  aria-current={active ? "page" : undefined}
                  className={cn(
                    "rounded-md px-3 py-2 text-sm font-medium transition-colors",
                    "focus:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background",
                    active
                      ? "bg-accent text-accent-foreground shadow-sm"
                      : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
                  )}
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
  // (garde si tu en as besoin plus tard)
  usePathname();

  return (
    <header className="sticky top-0 z-50 border-b bg-background/80 backdrop-blur supports-[backdrop-filter]:bg-background/60">
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
              className={cn(
                "h-9 w-56 cursor-default",
                "text-muted-foreground",
                "focus-visible:ring-0 focus-visible:ring-offset-0"
              )}
            />
          </div>

          <Button asChild variant="ghost">
            <Link href="/admin" className="text-muted-foreground hover:text-foreground">
              Admin <ArrowUpRight className="ml-2 h-4 w-4" />
            </Link>
          </Button>
        </div>
      </div>
    </header>
  );
}
