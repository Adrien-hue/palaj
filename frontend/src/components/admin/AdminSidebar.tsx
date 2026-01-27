"use client";

import * as React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Users, Briefcase, BadgeCheck, ArrowLeft, CirclePile } from "lucide-react";

import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarSeparator,
  useSidebar,
} from "@/components/ui/sidebar";

import { PalajBrand } from "@/components/layout/PalajBrand";

const nav = [
  { label: "Agents", href: "/admin/agents", icon: Users },
  { label: "Equipes", href: "/admin/teams", icon: CirclePile },
  { label: "Postes", href: "/admin/postes", icon: Briefcase },
  { label: "Régimes", href: "/admin/regimes", icon: BadgeCheck },
] as const;

export function AdminSidebar() {
  const pathname = usePathname();
  const { state } = useSidebar();
  const collapsed = state === "collapsed";

  return (
    <Sidebar collapsible="icon">
      {/* ===== Header / Brand ===== */}
      <SidebarHeader>
        <div className="px-2 py-1.5">
          <PalajBrand href="/admin" collapsed={collapsed} />
        </div>
      </SidebarHeader>

      <div className="px-2">
        <SidebarSeparator className="mx-0 w-full" />
      </div>

      {/* ===== Navigation ===== */}
      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel>Administration</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {nav.map((item) => {
                const active =
                  pathname === item.href || pathname.startsWith(item.href + "/");
                const Icon = item.icon;

                return (
                  <SidebarMenuItem key={item.href}>
                    <SidebarMenuButton
                      asChild
                      isActive={active}
                      tooltip={item.label}
                    >
                      <Link href={item.href}>
                        <Icon className="h-4 w-4" />
                        <span>{item.label}</span>
                      </Link>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                );
              })}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>

      <div className="px-2">
        <SidebarSeparator className="mx-0 w-full" />
      </div>

      {/* ===== Footer ===== */}
      <SidebarFooter>
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton asChild tooltip="Retour à l’app">
              <Link href="/app">
                <ArrowLeft className="h-4 w-4" />
                <span>Retour à l’app</span>
              </Link>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>

        {!collapsed && (
          <div className="px-3 py-2">
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              <span
                className="inline-flex h-2 w-2 rounded-full"
                style={{ backgroundColor: "var(--palaj-l)" }}
              />
              <span
                className="inline-flex h-2 w-2 rounded-full"
                style={{ backgroundColor: "var(--palaj-a)" }}
              />
              <span
                className="inline-flex h-2 w-2 rounded-full ring-1 ring-border"
                style={{ backgroundColor: "var(--palaj-j)" }}
              />
              <span>L • A • J</span>
            </div>
          </div>
        )}
      </SidebarFooter>
    </Sidebar>
  );
}
