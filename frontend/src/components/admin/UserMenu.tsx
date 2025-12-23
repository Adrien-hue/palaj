"use client";

import { useEffect, useRef, useState } from "react";

export default function UserMenu() {
  // Plus tard: injecter via ton auth (/me)
  const user = { name: "Admin", email: "admin@palaj.local" };

  const [open, setOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    function onPointerDown(e: PointerEvent) {
      const el = rootRef.current;
      if (!el) return;
      if (!el.contains(e.target as Node)) setOpen(false);
    }

    function onKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape") setOpen(false);
    }

    document.addEventListener("pointerdown", onPointerDown);
    document.addEventListener("keydown", onKeyDown);
    return () => {
      document.removeEventListener("pointerdown", onPointerDown);
      document.removeEventListener("keydown", onKeyDown);
    };
  }, []);

  return (
    <div ref={rootRef} className="relative">
      <button
        type="button"
        className="rounded-xl px-2 py-1 hover:bg-zinc-100"
        aria-haspopup="menu"
        aria-expanded={open}
        onClick={() => setOpen((v) => !v)}
      >
        <div className="flex items-center gap-3">
          <div className="grid h-9 w-9 place-items-center rounded-full bg-zinc-200 text-sm font-semibold text-zinc-700">
            {user.name.slice(0, 1).toUpperCase()}
          </div>
          <div className="hidden sm:block leading-tight text-left">
            <div className="text-sm font-medium">{user.name}</div>
            <div className="text-xs text-zinc-500">{user.email}</div>
          </div>
        </div>
      </button>

      {open && (
        <div
          role="menu"
          className="absolute right-0 mt-2 w-56 rounded-2xl bg-white p-1 shadow-lg ring-1 ring-zinc-200"
        >
          <a
            role="menuitem"
            className="block rounded-xl px-3 py-2 text-sm hover:bg-zinc-100"
            href="/admin/profil"
            onClick={() => setOpen(false)}
          >
            Profil
          </a>

          <button
            role="menuitem"
            className="w-full text-left block rounded-xl px-3 py-2 text-sm hover:bg-zinc-100 text-red-600"
            onClick={() => {
              setOpen(false);
              // TODO: vrai logout (clear cookie / refresh token)
              window.location.href = "/login";
            }}
          >
            Se déconnecter
          </button>
        </div>
      )}
    </div>
  );
}