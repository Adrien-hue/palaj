"use client";

import type { ReactNode } from "react";
import Topbar from "@/components/admin/Topbar";
import { AdminSidebar } from "@/components/admin/AdminSidebar";

import { SidebarInset, SidebarProvider } from "@/components/ui/sidebar";

export default function AdminLayout({ children }: { children: ReactNode }) {
  return (
    <SidebarProvider>
      <div className="flex h-dvh w-full overflow-hidden bg-background text-foreground">
        <AdminSidebar />

        <SidebarInset className="min-w-0">
          <Topbar />
          <main className="min-h-0 flex-1 overflow-hidden p-6">
            <div className="mx-auto h-full min-h-0 w-full max-w-6xl">
              {children}
            </div>
          </main>
        </SidebarInset>
      </div>
    </SidebarProvider>
  );
}
