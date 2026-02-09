// src/lib/relaySetCookies.ts
import { NextResponse } from "next/server";

export function relaySetCookies(upstream: Response, res: NextResponse) {
  const arr: string[] | undefined = upstream.headers.getSetCookie?.();
  if (arr?.length) {
    arr.forEach((c) => res.headers.append("set-cookie", c));
    return;
  }
  const single = upstream.headers.get("set-cookie");
  if (single) res.headers.append("set-cookie", single);
}
