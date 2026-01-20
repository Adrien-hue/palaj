import Link from "next/link";

import { ArrowUpRight } from "lucide-react";

type MenuCard = {
  title: string;
  description: string;
  href: string;
  accentVar: "var(--palaj-l)" | "var(--palaj-a)" | "var(--palaj-j)";
};

const CARDS: MenuCard[] = [
  {
    title: "Par agent",
    description: "Visualiser et modifier le planning agent par agent.",
    href: "/app/planning/agents",
    accentVar: "var(--palaj-l)",
  },
  {
    title: "Par poste",
    description: "Voir la couverture des postes et ajuster les affectations.",
    href: "/app/planning/postes",
    accentVar: "var(--palaj-a)",
  },
  {
    title: "Par groupe de postes",
    description: "Piloter le planning par groupe (équipe, secteur, roulement…).",
    href: "/app/planning/groupes",
    accentVar: "var(--palaj-j)",
  },
];

function MenuCardItem({ card }: { card: MenuCard }) {
  return (
    <Link
      href={card.href}
      className={[
        "group relative overflow-hidden rounded-xl",
        "border border-[color:var(--app-border)] bg-[color:var(--app-surface)] p-5 shadow-sm",
        "transition hover:-translate-y-0.5 hover:shadow-md",
        "active:translate-y-0 active:scale-[0.99]",
        "hover:ring-1 hover:ring-[color:var(--app-ring)] hover:ring-inset",
        "focus:outline-none focus-visible:ring-2 focus-visible:ring-[color:var(--app-focus)]",
      ].join(" ")}
    >
      {/* Accent bar (clipped by parent radius) */}
      <div
        className="absolute inset-y-0 left-0 w-1.5 opacity-80 transition group-hover:opacity-100"
        style={{ backgroundColor: card.accentVar }}
      />

      <div className="flex items-start justify-between gap-4">
        <div className="space-y-1">
          <h2 className="text-base font-semibold text-[color:var(--app-text)]">
            {card.title}
          </h2>
          <p className="text-sm leading-6 text-[color:var(--app-muted)]">
            {card.description}
          </p>
        </div>

        {/* Icon button: token-based for perfect light/dark contrast */}
        <div className="grid h-10 w-10 place-items-center rounded-xl bg-[color:var(--app-soft)] text-[color:var(--app-soft-text)] transition group-hover:bg-[color:var(--app-soft-hover)] group-hover:text-[color:var(--app-soft-text-hover)]">
            <ArrowUpRight
                className="h-4 w-4 transition-transform group-hover:-translate-y-0.5 group-hover:translate-x-0.5"
                strokeWidth={2}
            />
        </div>
      </div>

      <div className="mt-4 flex items-center justify-between">
        <span className="text-sm font-medium text-[color:var(--app-muted)] transition group-hover:text-[color:var(--app-text)]">
          Ouvrir
        </span>
        <span className="text-sm text-[color:var(--app-faint)] transition group-hover:translate-x-0.5 group-hover:text-[color:var(--app-muted)]">
          →
        </span>
      </div>
    </Link>
  );
}

export default function AppHomePage() {
  return (
    <div className="space-y-6">
      <header className="space-y-2">
        <h1 className="text-2xl font-semibold tracking-tight text-[color:var(--app-text)]">
          Planning
        </h1>
        <p className="max-w-2xl text-[color:var(--app-muted)]">
          Choisis une vue pour consulter et modifier les plannings.
        </p>
      </header>

      <section className="grid gap-4 md:grid-cols-3">
        {CARDS.map((card) => (
          <MenuCardItem key={card.href} card={card} />
        ))}
      </section>

      <section className="rounded-xl border border-[color:var(--app-border)] bg-[color:var(--app-surface)] p-5">
        <div className="text-sm font-medium text-[color:var(--app-text)]">
          Astuce
        </div>
        <p className="mt-1 text-sm text-[color:var(--app-muted)]">
          La vue “par agent” est idéale pour les ajustements au fil de l’eau.
          Ensuite, on utilisera “par poste” pour vérifier la couverture et
          équilibrer la charge.
        </p>
      </section>
    </div>
  );
}
