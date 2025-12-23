"use client";

import type { ReactNode } from "react";
import { useState } from "react";

import Sidebar from "@/components/admin/Sidebar";
import Topbar from "@/components/admin/Topbar";

export default function AdminLayout({ children }: { children: ReactNode }) {
  const [collapsed, setCollapsed] = useState(false);

  return (
    <div className="min-h-dvh bg-zinc-50 text-zinc-900">
      <div className="flex min-h-dvh">
        <Sidebar collapsed={collapsed} setCollapsed={setCollapsed} />

        <div className="flex min-w-0 flex-1 flex-col">
          <Topbar />
          <main className="flex-1 p-6">
            <div className="mx-auto w-full max-w-6xl">{children}</div>
          </main>
        </div>
      </div>
    </div>
  );
}
