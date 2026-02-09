import { NextResponse } from "next/server";
import { cookies } from "next/headers";
import { relaySetCookies } from "@/lib/relaySetCookies";

const BACKEND_URL = process.env.BACKEND_URL!;

export async function POST() {
  const cookieStore = await cookies();
  const cookieHeader = cookieStore
    .getAll()
    .map((c) => `${c.name}=${c.value}`)
    .join("; ");

  const upstream = await fetch(`${BACKEND_URL}/api/v1/auth/logout`, {
    method: "POST",
    headers: {
      ...(cookieHeader ? { Cookie: cookieHeader } : {}),
      Accept: "application/json",
    },
  });

  const data = await upstream.json().catch(() => null);
  const res = NextResponse.json(data, { status: upstream.status });

  relaySetCookies(upstream, res);
  return res;
}
