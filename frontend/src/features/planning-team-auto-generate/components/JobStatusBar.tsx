"use client";

import * as React from "react";
import { Bug, Copy, Loader2, RefreshCw, TriangleAlert } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";

import type { JobStatus } from "../hooks/useTeamPlanningGenerate";

type DebugTab = "status" | "stats" | "errors" | "history";
type DebugIndicator = "error" | "success" | "busy" | "none";

type JobStatusBarProps = {
  status?: JobStatus | null;
  jobId?: string | null;
  draftId?: number | null;
  isBusy?: boolean;
  hasError?: boolean;
  debugEnabled: boolean;
  debugIndicator: DebugIndicator;
  startedAtMs?: number | null;
  finishedAtMs?: number | null;
  onCopyJobId?: () => void;
  onCopyContext?: () => void;
  onRefresh?: () => void;
  onOpenDebug?: (tab?: DebugTab) => void;
  onScrollToPlanning?: () => void;
  helperText?: string;
};

function getStatusContent(status?: JobStatus | null) {
  if (status === "queued" || status === "running") {
    return { label: "queued", text: "Génération en cours", variant: "secondary" as const };
  }
  if (status === "success") {
    return { label: "success", text: "Terminé", variant: "success" as const };
  }
  if (status === "failed") {
    return { label: "failed", text: "Échec", variant: "destructive" as const };
  }
  return { label: "status", text: "Statut inconnu", variant: "outline" as const };
}

function shortenJobId(jobId: string) {
  if (jobId.length <= 14) return jobId;
  return `${jobId.slice(0, 8)}…${jobId.slice(-4)}`;
}

function formatDuration(totalSeconds: number, prefix: "depuis" | "durée") {
  if (totalSeconds < 60) return `${prefix} ${totalSeconds}s`;

  if (totalSeconds < 3600) {
    const minutes = Math.floor(totalSeconds / 60);
    const seconds = totalSeconds % 60;
    return `${prefix} ${minutes}m ${String(seconds).padStart(2, "0")}s`;
  }

  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  return `${prefix} ${hours}h ${String(minutes).padStart(2, "0")}m`;
}

function useNowTick(isActive: boolean) {
  const [nowMs, setNowMs] = React.useState(() => Date.now());

  React.useEffect(() => {
    if (!isActive) return;

    const id = window.setInterval(() => {
      setNowMs(Date.now());
    }, 1000);

    return () => window.clearInterval(id);
  }, [isActive]);

  React.useEffect(() => {
    if (isActive) return;
    setNowMs(Date.now());
  }, [isActive]);

  return nowMs;
}

function getDebugIndicatorUi(debugIndicator: DebugIndicator) {
  if (debugIndicator === "error") {
    return {
      ariaLabel: "Debug: erreurs détectées",
      node: (
        <Badge variant="destructive" className="h-5 min-w-5 px-1 text-[10px] leading-none">
          !
        </Badge>
      ),
    };
  }

  if (debugIndicator === "success") {
    return {
      ariaLabel: "Debug: statut succès avec stats",
      node: (
        <Badge variant="success" className="h-5 px-1.5 text-[10px] leading-none">
          OK
        </Badge>
      ),
    };
  }

  if (debugIndicator === "busy") {
    return {
      ariaLabel: "Debug: génération en cours",
      node: (
        <Badge variant="secondary" className="h-5 min-w-5 px-1 text-[10px] leading-none">
          <Loader2 className="h-3 w-3 animate-spin" />
        </Badge>
      ),
    };
  }

  return { ariaLabel: "Debug", node: null };
}

export function JobStatusBar({
  status = null,
  jobId = null,
  draftId = null,
  isBusy = false,
  hasError = false,
  debugEnabled,
  debugIndicator,
  startedAtMs = null,
  finishedAtMs = null,
  onCopyJobId,
  onCopyContext,
  onRefresh,
  onOpenDebug,
  onScrollToPlanning,
  helperText,
}: JobStatusBarProps) {
  const statusContent = React.useMemo(() => getStatusContent(status), [status]);
  const jobIdShort = React.useMemo(() => (jobId ? shortenJobId(jobId) : null), [jobId]);
  const shouldTick = status === "queued" || status === "running";
  const nowMs = useNowTick(shouldTick);

  const durationLabel = React.useMemo(() => {
    if (!startedAtMs) return null;

    if (shouldTick) {
      const elapsedSeconds = Math.max(0, Math.floor((nowMs - startedAtMs) / 1000));
      return formatDuration(elapsedSeconds, "depuis");
    }

    if (finishedAtMs) {
      const elapsedSeconds = Math.max(0, Math.floor((finishedAtMs - startedAtMs) / 1000));
      return formatDuration(elapsedSeconds, "durée");
    }

    return null;
  }, [finishedAtMs, nowMs, shouldTick, startedAtMs]);

  const debugUi = React.useMemo(() => getDebugIndicatorUi(debugIndicator), [debugIndicator]);
  const debugTooltipText = React.useMemo(() => {
    if (debugIndicator === "error") return "Ouvrir debug (erreurs détectées)";
    if (debugIndicator === "success") return "Ouvrir debug (stats disponibles)";
    if (debugIndicator === "busy") return "Ouvrir debug (job en cours)";
    return "Ouvrir debug";
  }, [debugIndicator]);

  return (
    <div className="sticky top-0 z-10 flex items-center justify-between gap-2 border-b bg-background/95 px-3 py-2 backdrop-blur">
      <div className="flex min-w-0 items-center gap-2 text-sm">
        <Badge variant={statusContent.variant} className="gap-1">
          {isBusy ? <Loader2 className="h-3 w-3 animate-spin" /> : null}
          {statusContent.label}
        </Badge>
        <span className="text-muted-foreground">{statusContent.text}</span>
        {jobIdShort ? <span className="truncate text-xs text-muted-foreground">job {jobIdShort}</span> : null}
        {status === "success" && draftId ? (
          <Badge variant="outline" className="text-xs">
            Draft #{draftId}
          </Badge>
        ) : null}
        {durationLabel ? <span className="text-xs text-muted-foreground">{durationLabel}</span> : null}
        {helperText ? <span className="hidden text-xs text-muted-foreground md:inline">{helperText}</span> : null}
      </div>

      <div className="flex shrink-0 items-center gap-1">
        {onCopyJobId && jobId ? (
          <Tooltip>
            <TooltipTrigger asChild>
              <Button type="button" variant="ghost" size="icon" aria-label="Copier ID job" onClick={onCopyJobId}>
                <Copy className="h-4 w-4" />
              </Button>
            </TooltipTrigger>
            <TooltipContent>Copier ID</TooltipContent>
          </Tooltip>
        ) : null}

        {onCopyContext ? (
          <Button type="button" variant="ghost" size="sm" onClick={onCopyContext}>
            Copier contexte
          </Button>
        ) : null}

        {debugEnabled && onOpenDebug ? (
          <Tooltip>
            <TooltipTrigger asChild>
              <div className="relative inline-flex">
                <Button type="button" variant="ghost" size="sm" onClick={() => onOpenDebug("status")}>
                  <Bug className="mr-1 h-4 w-4" />
                  Debug
                </Button>
                {debugUi.node ? (
                  <span
                    aria-label={debugUi.ariaLabel}
                    className="absolute -right-1 -top-1"
                    role="status"
                  >
                    {debugUi.node}
                  </span>
                ) : null}
              </div>
            </TooltipTrigger>
            <TooltipContent>{debugTooltipText}</TooltipContent>
          </Tooltip>
        ) : null}

        {onRefresh ? (
          <Button type="button" variant="ghost" size="sm" onClick={onRefresh}>
            <RefreshCw className="mr-1 h-4 w-4" />
            Rafraîchir
          </Button>
        ) : null}

        {hasError && onOpenDebug ? (
          <Button type="button" variant="outline" size="sm" onClick={() => onOpenDebug("errors")}>
            <TriangleAlert className="mr-1 h-4 w-4" />
            Voir erreurs
          </Button>
        ) : null}

        {status === "success" && draftId && onScrollToPlanning ? (
          <Button type="button" variant="outline" size="sm" onClick={onScrollToPlanning}>
            Aller au planning
          </Button>
        ) : null}
      </div>
    </div>
  );
}

export type { DebugIndicator, DebugTab };
