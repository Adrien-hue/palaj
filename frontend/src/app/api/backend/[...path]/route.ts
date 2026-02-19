import { NextResponse } from "next/server";
import { cookies } from "next/headers";
import { relaySetCookies } from "@/lib/relaySetCookies";

import { env } from "@/config/env";

const BACKEND_URL = env.BACKEND_URL!;
if (!BACKEND_URL) throw new Error("Missing BACKEND_URL in env");

type Params = { path?: string[] };
type Ctx = { params: Params } | { params: Promise<Params> };

function buildCookieHeader(cookieStore: Awaited<ReturnType<typeof cookies>>) {
  // cookieStore.getAll() => [{name,value}, ...]
  const all = cookieStore.getAll();
  if (!all.length) return "";
  return all.map((c) => `${c.name}=${c.value}`).join("; ");
}

async function handler(req: Request, ctx: Ctx) {
  const url = new URL(req.url);

  // unwrap params (Next may provide params as Promise)
  const params = "then" in (ctx as any).params ? await (ctx as any).params : (ctx as any).params;
  const pathParts = Array.isArray(params?.path) ? params.path : [];

  // unwrap cookies (Next dynamic API may be async)
  const cookieStore = await cookies();
  const cookieHeader = buildCookieHeader(cookieStore);

  const target = `${BACKEND_URL}/${pathParts.join("/")}${url.search}`;

  const upstream = await fetch(target, {
    method: req.method,
    headers: {
      ...(cookieHeader ? { Cookie: cookieHeader } : {}),
      Accept: req.headers.get("accept") ?? "application/json",
      "Content-Type": req.headers.get("content-type") ?? "application/json",
    },
    body: ["GET", "HEAD"].includes(req.method) ? undefined : await req.text(),
  });

  const contentType = upstream.headers.get("content-type") ?? "";
  const isJson = contentType.includes("application/json");

  const body = isJson ? await upstream.json().catch(() => null) : await upstream.text();

  const res = isJson
    ? NextResponse.json(body, { status: upstream.status })
    : new NextResponse(body, { status: upstream.status });

  relaySetCookies(upstream, res);
  return res;
}

export const GET = handler;
export const POST = handler;
export const PUT = handler;
export const PATCH = handler;
export const DELETE = handler;
