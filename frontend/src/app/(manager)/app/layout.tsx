// src/app/(manager)/app/layout.tsx
import { AppTopbar } from "@/components/layout/AppTopbar";

export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-zinc-50">
      <AppTopbar />
      <main className="mx-auto w-full max-w-[1600px] px-6 py-6">
        {children}
      </main>
    </div>
  );
}
