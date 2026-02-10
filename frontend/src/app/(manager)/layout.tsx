import { ReactNode } from "react";
import { redirectOnAuthError } from "@/lib/api/redirectOnAuthError";

type Props = {
  children: ReactNode;
};

export default async function ManagerLayout({ children }: Props) {
  try {
    return <>{children}</>;
  } catch (e) {
    redirectOnAuthError(e);
  }
}
