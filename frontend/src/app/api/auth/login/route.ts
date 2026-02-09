import { NextResponse } from "next/server";
import { relaySetCookies } from "@/lib/relaySetCookies";

const BACKEND_URL = process.env.BACKEND_URL!;

export async function POST(req: Request) {
  const body = await req.json();

  const upstream = await fetch(`${BACKEND_URL}/api/v1/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  const data = await upstream.json().catch(() => null);
  const res = NextResponse.json(data, { status: upstream.status });

  relaySetCookies(upstream, res);
  return res;
}
