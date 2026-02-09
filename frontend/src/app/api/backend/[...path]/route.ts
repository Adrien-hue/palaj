import { NextResponse } from "next/server";
import { cookies } from "next/headers";
import { relaySetCookies } from "@/lib/relaySetCookies";

const BACKEND_URL = process.env.BACKEND_URL!;

async function handler(req: Request, ctx: { params: { path: string[] } }) {
  const url = new URL(req.url);
  const target = `${BACKEND_URL}/${ctx.params.path.join("/")}${url.search}`;

  const upstream = await fetch(target, {
    method: req.method,
    headers: {
      Cookie: cookies().toString(),
      "Content-Type": req.headers.get("content-type") ?? "application/json",
      Accept: req.headers.get("accept") ?? "application/json",
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
