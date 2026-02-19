// frontend/src/config/env.ts
export const env = {
  NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL,
  NEXT_PUBLIC_APP_URL: process.env.NEXT_PUBLIC_APP_URL,
  BACKEND_URL: process.env.BACKEND_URL,
} as const;

// Optionnel : helper de validation
export function assertPublicEnv() {
  if (!env.NEXT_PUBLIC_API_URL) throw new Error("Missing NEXT_PUBLIC_API_URL");
  if (!env.NEXT_PUBLIC_APP_URL) throw new Error("Missing NEXT_PUBLIC_APP_URL");
}

// BACKEND_URL est server-side : soit tu ne le valides pas ici,
// soit tu le valides uniquement côté serveur quand tu en as besoin.
export function assertServerEnv() {
  if (!env.BACKEND_URL) throw new Error("Missing BACKEND_URL");
}
