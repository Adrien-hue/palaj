import { redirect } from "next/navigation";
import { UnauthorizedError, AuthExpiredError } from "./errors";

export function redirectOnAuthError(e: unknown, next?: string): never {
  if (e instanceof UnauthorizedError || e instanceof AuthExpiredError) {
    const reason = "expired";
    const suffix = next ? `&next=${encodeURIComponent(next)}` : "";
    redirect(`/login?reason=${reason}${suffix}`);
  }
  throw e;
}
