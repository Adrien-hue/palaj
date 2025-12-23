"use client";

import type { ReactNode } from "react";
import { useState } from "react";
import Sidebar from "@/components/admin/Sidebar";
import Topbar from "@/components/admin/Topbar";

export default function AdminLayout({ children }: { children: ReactNode }) {
  const [collapsed, setCollapsed] = useState(false);

  return (
    <div className="h-dvh overflow-hidden bg-zinc-50 text-zinc-900">
      <div className="flex h-full min-h-0">
        <Sidebar collapsed={collapsed} setCollapsed={setCollapsed} />

        <div className="flex min-w-0 flex-1 min-h-0 flex-col">
          <Topbar />

          <main className="min-h-0 flex-1 overflow-hidden p-6">
            <div className="mx-auto h-full min-h-0 w-full max-w-6xl">
              {children}
            </div>
          </main>
        </div>
      </div>
    </div>
  );
}
