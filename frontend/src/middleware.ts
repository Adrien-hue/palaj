import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

const PUBLIC_PATHS = [
  "/login",
  "/favicon.ico",
  "/robots.txt",
  "/sitemap.xml",
];

function isPublicPath(pathname: string) {
  // Autorise toutes les routes publiques exactes
  if (PUBLIC_PATHS.includes(pathname)) return true;

  // Autorise les assets statiques usuels (si tu en as)
  if (pathname.startsWith("/_next/")) return true;
  if (pathname.startsWith("/api/")) return true; // IMPORTANT: ne pas bloquer tes route handlers Next
  if (pathname.startsWith("/public/")) return true; // optionnel, selon ton setup

  // Autorise les fichiers statiques par extension (images/fonts)
  if (/\.(png|jpg|jpeg|gif|webp|svg|ico|css|js|map|woff2?|ttf|eot)$/.test(pathname)) {
    return true;
  }

  return false;
}

export function middleware(req: NextRequest) {
  const { pathname } = req.nextUrl;

  // Laisse passer ce qui est public / infra
  if (isPublicPath(pathname)) {
    return NextResponse.next();
  }

  // Token d’accès en cookie httpOnly (posé par le backend)
  const hasAccessToken = req.cookies.has("palaj_at");

  if (hasAccessToken) {
    return NextResponse.next();
  }

  // Sinon => redirect login + retour à la page demandée
  const loginUrl = req.nextUrl.clone();
  loginUrl.pathname = "/login";
  loginUrl.searchParams.set("next", pathname + req.nextUrl.search);

  return NextResponse.redirect(loginUrl);
}

// Applique le middleware partout sauf ce qu'on exclut via matcher.
export const config = {
  matcher: [
    // Tout, sauf _next static, images, favicon etc. (on filtre aussi via isPublicPath)
    "/((?!_next).*)",
  ],
};
