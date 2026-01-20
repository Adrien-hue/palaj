// src/navigation/appNav.ts
export type AppNavItem = {
  label: string;
  href: string;
};

export const APP_TOP_NAV: AppNavItem[] = [
  { label: "Planning", href: "/app/planning/agents" },
  // Tu pourras ajouter plus tard :
  // { label: "Référentiels", href: "/admin" },
  // { label: "Paramètres", href: "/app/settings" },
];

export const PLANNING_TABS: AppNavItem[] = [
  { label: "Par agent", href: "/app/planning/agents" },
  { label: "Par poste", href: "/app/planning/postes" },
  { label: "Par groupe", href: "/app/planning/groupes" },
];
