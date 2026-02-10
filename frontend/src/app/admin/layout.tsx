import type { ReactNode } from "react";
import { redirectOnAuthError } from "@/lib/api/redirectOnAuthError";
import AdminShell from "@/components/admin/AdminShell";

type Props = { children: ReactNode };

export default function AdminLayout({ children }: Props) {
  try {
    return <AdminShell>{children}</AdminShell>;
  } catch (e) {
    redirectOnAuthError(e);
  }
}
