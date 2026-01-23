import Link from "next/link";
import { ArrowUpRight, ChevronRight } from "lucide-react";

import { Card, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

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
    title: "Par équipe",
    description: "Piloter le planning par équipe.",
    href: "/app/planning/groupes",
    accentVar: "var(--palaj-j)",
  },
];

function MenuCardItem({ card }: { card: MenuCard }) {
  return (
    <Card
      className={[
        "group relative overflow-hidden rounded-xl",
        "border-[color:var(--app-border)] bg-[color:var(--app-surface)] shadow-sm",
        "transition",
        "hover:-translate-y-0.5 hover:shadow-md",
        "hover:ring-1 hover:ring-[color:var(--app-ring)] hover:ring-inset",
        "focus-within:ring-2 focus-within:ring-[color:var(--app-focus)]",
        "active:translate-y-0 active:scale-[0.99]",
      ].join(" ")}
    >
      {/* Accent bar - full height of card */}
      <div
        className="absolute inset-y-0 left-0 w-2.5 opacity-80 transition group-hover:opacity-100"
        style={{ backgroundColor: card.accentVar }}
        aria-hidden="true"
      />

      {/* Stretched link: makes the whole card clickable + hover/focus works everywhere */}
      <Link
        href={card.href}
        className="absolute inset-0 z-10 rounded-xl focus:outline-none"
        aria-label={`Ouvrir ${card.title}`}
      />

      <CardHeader className="relative z-0 pb-3">
        <div className="flex items-start justify-between gap-4">
          <div className="min-w-0 space-y-1">
            <CardTitle className="text-base text-[color:var(--app-text)]">
              {card.title}
            </CardTitle>
            <p className="text-sm leading-6 text-[color:var(--app-muted)]">
              {card.description}
            </p>
          </div>

          {/* purely decorative/action-looking, but click goes to the stretched link */}
          <Button
            type="button"
            tabIndex={-1}
            aria-hidden="true"
            variant="secondary"
            size="icon"
            className={[
              "h-10 w-10 rounded-xl",
              "border border-[color:var(--app-border)]",
              "bg-[color:var(--app-soft)] text-[color:var(--app-soft-text)]",
              "hover:bg-[color:var(--app-soft-hover)] hover:text-[color:var(--app-soft-text-hover)]",
              "pointer-events-none", // avoid nested interactive inside link overlay
            ].join(" ")}
          >
            <ArrowUpRight
              className="h-4 w-4 transition-transform group-hover:-translate-y-0.5 group-hover:translate-x-0.5"
              strokeWidth={2}
            />
          </Button>
        </div>
      </CardHeader>

      <CardFooter className="relative z-0 flex items-center justify-between pt-0">
        <span className="text-sm font-medium text-[color:var(--app-muted)] transition group-hover:text-[color:var(--app-text)]">
          Ouvrir
        </span>

        <span className="inline-flex items-center gap-1 text-sm text-[color:var(--app-faint)] transition group-hover:translate-x-0.5 group-hover:text-[color:var(--app-muted)]">
          <ChevronRight className="h-4 w-4" />
        </span>
      </CardFooter>
    </Card>
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
    </div>
  );
}
