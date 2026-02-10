import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

const ACCESS_COOKIE = "palaj_at";
const REFRESH_COOKIE = "palaj_rt";

const PUBLIC_PATHS = ["/login", "/favicon.ico", "/robots.txt", "/sitemap.xml"];

function isPublicPath(pathname: string) {
  if (PUBLIC_PATHS.includes(pathname)) return true;
  if (pathname.startsWith("/_next/")) return true;
  if (pathname.startsWith("/api/")) return true;
  if (pathname.startsWith("/public/")) return true;
  if (/\.(png|jpg|jpeg|gif|webp|svg|ico|css|js|map|woff2?|ttf|eot)$/.test(pathname)) return true;
  return false;
}

function buildLoginRedirect(req: NextRequest) {
  const loginUrl = req.nextUrl.clone();
  loginUrl.pathname = "/login";
  loginUrl.searchParams.set("reason", "expired");
  loginUrl.searchParams.set("next", req.nextUrl.pathname + req.nextUrl.search);
  return NextResponse.redirect(loginUrl);
}

function relaySetCookieHeaders(upstream: Response, downstream: NextResponse) {
  const anyHeaders = upstream.headers as any;
  const setCookies: string[] =
    typeof anyHeaders.getSetCookie === "function"
      ? anyHeaders.getSetCookie()
      : upstream.headers.get("set-cookie")
        ? [upstream.headers.get("set-cookie") as string]
        : [];

  for (const sc of setCookies) {
    if (sc) downstream.headers.append("set-cookie", sc);
  }
}

export async function middleware(req: NextRequest) {
  const { pathname } = req.nextUrl;

  if (isPublicPath(pathname)) return NextResponse.next();

  if (req.cookies.has(ACCESS_COOKIE)) return NextResponse.next();

  if (req.nextUrl.searchParams.get("__rf") === "1") {
    return buildLoginRedirect(req);
  }

  if (!req.cookies.has(REFRESH_COOKIE)) {
    return buildLoginRedirect(req);
  }

  const refreshUrl = req.nextUrl.clone();
  refreshUrl.pathname = "/api/auth/refresh";
  refreshUrl.search = "";

  const cookieHeader = req.cookies
    .getAll()
    .map((c) => `${c.name}=${c.value}`)
    .join("; ");

  const upstream = await fetch(refreshUrl, {
    method: "POST",
    headers: {
      ...(cookieHeader ? { Cookie: cookieHeader } : {}),
      Accept: "application/json",
    },
  });

  if (!upstream.ok) {
    return buildLoginRedirect(req);
  }

  const retryUrl = req.nextUrl.clone();
  retryUrl.searchParams.set("__rf", "1");

  const res = NextResponse.redirect(retryUrl, { status: 307 });
  relaySetCookieHeaders(upstream, res);
  return res;
}

export const config = {
  matcher: ["/((?!_next).*)"],
};
