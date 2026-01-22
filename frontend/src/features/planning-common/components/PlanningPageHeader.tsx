"use client";

import Link from "next/link";
import { ChevronLeft } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb";

import { usePlanningMonthParam } from "@/features/planning-common/hooks/usePlanningMonthParam";

type Crumb = { label: string; href?: string };

export function PlanningPageHeader({
  crumbs,
  backHref,
  backLabel = "Retour",
  title,
  subtitle,
  controls,
}: {
  crumbs: Crumb[];
  backHref: string;
  backLabel?: string;
  title: string;
  subtitle?: string;
  controls?: React.ReactNode;
}) {
  const { label: monthLabel } = usePlanningMonthParam();

  return (
    <Card className="border-[color:var(--app-border)] bg-[color:var(--app-surface)] shadow-sm">
      <CardHeader className="gap-2">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <Breadcrumb>
            <BreadcrumbList className="text-[color:var(--app-muted)]">
              {crumbs.map((c, idx) => {
                const isLast = idx === crumbs.length - 1;

                return (
                  <div key={`${c.label}-${idx}`} className="contents">
                    <BreadcrumbItem>
                      {!isLast && c.href ? (
                        <BreadcrumbLink asChild>
                          <Link
                            href={c.href}
                            className="rounded-md px-1.5 py-0.5 transition hover:bg-[color:var(--app-soft)] hover:text-[color:var(--app-text)]"
                          >
                            {c.label}
                          </Link>
                        </BreadcrumbLink>
                      ) : (
                        <BreadcrumbPage className="font-medium text-[color:var(--app-text)]">
                          {c.label}
                        </BreadcrumbPage>
                      )}
                    </BreadcrumbItem>

                    {!isLast ? <BreadcrumbSeparator /> : null}
                  </div>
                );
              })}
            </BreadcrumbList>
          </Breadcrumb>

          <Badge variant="secondary" className="h-7 px-3 text-sm font-medium">
            {monthLabel}
          </Badge>
        </div>

        <Button
          asChild
          variant="outline"
          size="sm"
          className="h-8 w-fit px-2 text-[color:var(--app-muted)] hover:text-[color:var(--app-text)]"
        >
          <Link href={backHref} aria-label={backLabel}>
            <ChevronLeft className="mr-1 h-4 w-4" />
            {backLabel}
          </Link>
        </Button>
      </CardHeader>

      <CardContent className="pt-0">
        <div className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <h1 className="text-2xl font-semibold text-[color:var(--app-text)]">
              {title}
            </h1>
            {subtitle ? (
              <p className="text-sm text-[color:var(--app-muted)]">
                {subtitle}
              </p>
            ) : null}
          </div>

          {controls ? <div>{controls}</div> : null}
        </div>
      </CardContent>
    </Card>
  );
}
