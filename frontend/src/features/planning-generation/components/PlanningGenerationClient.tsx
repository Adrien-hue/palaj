"use client";

import * as React from "react";
import { differenceInCalendarDays, endOfMonth, format, startOfMonth } from "date-fns";
import { Loader2, Sparkles } from "lucide-react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { toast } from "sonner";

import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";
import { PlanningPeriodControls } from "@/features/planning-common/period/PlanningPeriodControls";
import type { PlanningPeriod } from "@/features/planning-common/period/period.types";
import { shiftPlanningPeriod } from "@/features/planning-common/period/period.utils";
import { TeamHeaderSelect } from "@/features/planning-team/components/TeamHeaderSelect";
import { TeamPlanningMatrix } from "@/features/planning-team/components/TeamPlanningMatrix";
import { buildTeamPlanningVm } from "@/features/planning-team/vm/teamPlanning.vm.builder";
import { ApiError } from "@/lib/api/errors";
import { toISODate } from "@/utils/date.format";

import { useAcceptDraft } from "../hooks/useAcceptDraft";
import { useDraftTeamPlanning } from "../hooks/useDraftTeamPlanning";
import { useGeneratePlanningJob } from "../hooks/useGeneratePlanningJob";
import { usePlanningJobStatus } from "../hooks/usePlanningJobStatus";
import { useRejectDraft } from "../hooks/useRejectDraft";
import { useTeams } from "../hooks/useTeams";

const LAST_JOB_STORAGE_KEY = "palaj:last_planning_generation_job_id";

type DraftResolution = "accepted" | "rejected" | null;

function clampProgress(progress?: number) {
  if (typeof progress !== "number" || Number.isNaN(progress)) return null;
  return Math.max(0, Math.min(1, progress));
}

function parseResolutionFromUnknown(payload: unknown): DraftResolution {
  if (!payload || typeof payload !== "object") return null;
  const status = (payload as { status?: unknown }).status;
  if (status === "accepted" || status === "rejected") return status;
  return null;
}

function getApiErrorMessage(error: unknown) {
  if (!(error instanceof ApiError)) {
    return error instanceof Error ? error.message : "Erreur inconnue";
  }

  if (error.status === 409) return "Action impossible: draft déjà traité";
  if (error.status === 403) return "Non autorisé";
  if (error.status === 404) return "Draft introuvable";

  if (typeof error.detail === "string" && error.detail.length > 0) {
    return error.detail;
  }

  return error.message;
}

export function PlanningGenerationClient() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  const teamsQuery = useTeams();
  const generateMutation = useGeneratePlanningJob();

  const [teamId, setTeamId] = React.useState<number | null>(null);
  const [jobId, setJobId] = React.useState<string | null>(null);
  const [isConfirmGenerateOpen, setIsConfirmGenerateOpen] = React.useState(false);
  const [isConfirmAcceptOpen, setIsConfirmAcceptOpen] = React.useState(false);
  const [isConfirmRejectOpen, setIsConfirmRejectOpen] = React.useState(false);
  const [lastUpdatedAt, setLastUpdatedAt] = React.useState<Date | null>(null);
  const [draftResolution, setDraftResolution] = React.useState<DraftResolution>(null);
  const [isAlreadyDecided, setIsAlreadyDecided] = React.useState(false);

  const [period, setPeriod] = React.useState<PlanningPeriod>({
    kind: "month",
    month: startOfMonth(new Date()),
  });

  const range = React.useMemo(() => {
    if (period.kind === "month") {
      return {
        startDate: toISODate(startOfMonth(period.month)),
        endDate: toISODate(endOfMonth(period.month)),
      };
    }

    return {
      startDate: toISODate(period.start),
      endDate: toISODate(period.end),
    };
  }, [period]);

  const periodDays = React.useMemo(() => {
    const start = new Date(`${range.startDate}T00:00:00`);
    const end = new Date(`${range.endDate}T00:00:00`);
    return differenceInCalendarDays(end, start) + 1;
  }, [range.endDate, range.startDate]);

  const hasInvalidPeriod = range.startDate > range.endDate;
  const hasLongPeriod = !hasInvalidPeriod && periodDays > 31;

  const updateJobInUrl = React.useCallback(
    (nextJobId: string | null) => {
      const params = new URLSearchParams(searchParams.toString());
      if (nextJobId) params.set("job", nextJobId);
      else params.delete("job");

      const queryString = params.toString();
      router.replace(queryString ? `${pathname}?${queryString}` : pathname, { scroll: false });
    },
    [pathname, router, searchParams],
  );

  React.useEffect(() => {
    const jobFromQuery = searchParams.get("job");

    if (jobFromQuery) {
      setJobId((prev) => (prev === jobFromQuery ? prev : jobFromQuery));
      if (typeof window !== "undefined") {
        window.localStorage.setItem(LAST_JOB_STORAGE_KEY, jobFromQuery);
      }
      return;
    }

    if (typeof window === "undefined") return;

    const storedJobId = window.localStorage.getItem(LAST_JOB_STORAGE_KEY);
    if (!storedJobId) return;

    setJobId((prev) => (prev === storedJobId ? prev : storedJobId));
    updateJobInUrl(storedJobId);
  }, [searchParams, updateJobInUrl]);

  const jobQuery = usePlanningJobStatus(jobId);
  const status = jobQuery.data?.status;
  const isJobRunning = status === "queued" || status === "running";

  React.useEffect(() => {
    if (!jobQuery.data) return;
    setLastUpdatedAt(new Date());
  }, [jobQuery.data]);

  const draftId = jobQuery.data?.draft_id && jobQuery.data.draft_id > 0 ? jobQuery.data.draft_id : null;
  const draftQuery = useDraftTeamPlanning(draftId, status === "success");
  const acceptDraftMutation = useAcceptDraft(draftId);
  const rejectDraftMutation = useRejectDraft(draftId);

  React.useEffect(() => {
    setDraftResolution(null);
    setIsAlreadyDecided(false);
  }, [draftId]);

  const isDecisionMutating = acceptDraftMutation.isMutating || rejectDraftMutation.isMutating;
  const isParametersLocked = isJobRunning || isDecisionMutating;

  const planningVm = React.useMemo(() => {
    if (!draftQuery.data) return null;
    return buildTeamPlanningVm(draftQuery.data);
  }, [draftQuery.data]);

  const isPlanningVisible = status === "success" && Boolean(planningVm);

  const canGenerate =
    teamId !== null && !hasInvalidPeriod && !isJobRunning && !generateMutation.isMutating && !isDecisionMutating;

  const canShowDraftActions =
    status === "success" && Boolean(draftId) && !draftQuery.isLoading && Boolean(planningVm);

  const actionsLocked = isJobRunning || draftResolution !== null || isAlreadyDecided || isDecisionMutating;

  const runGeneration = React.useCallback(async () => {
    if (!teamId || hasInvalidPeriod) return;

    setDraftResolution(null);
    setIsAlreadyDecided(false);

    try {
      const response = await generateMutation.trigger({
        team_id: teamId,
        start_date: range.startDate,
        end_date: range.endDate,
      });

      setJobId(response.job_id);
      updateJobInUrl(response.job_id);

      if (typeof window !== "undefined") {
        window.localStorage.setItem(LAST_JOB_STORAGE_KEY, response.job_id);
      }

      toast.success("Génération lancée", {
        description: `Job ${response.job_id}`,
      });
    } catch (error) {
      toast.error("Échec du lancement de génération", {
        description: error instanceof Error ? error.message : "Erreur inconnue",
      });
    }
  }, [generateMutation, hasInvalidPeriod, range.endDate, range.startDate, teamId, updateJobInUrl]);

  const handleGenerateNew = React.useCallback(() => {
    if (isPlanningVisible) {
      setIsConfirmGenerateOpen(true);
      return;
    }

    void runGeneration();
  }, [isPlanningVisible, runGeneration]);

  const refreshAfterDraftDecision = React.useCallback(async () => {
    await Promise.all([jobQuery.mutate(), draftQuery.mutate()]);
  }, [draftQuery, jobQuery]);

  const handleAcceptDraft = React.useCallback(async () => {
    if (!draftId) return;

    try {
      const response = await acceptDraftMutation.trigger();
      const resolved = parseResolutionFromUnknown(response);
      setDraftResolution(resolved);
      setIsAlreadyDecided(resolved === null);
      toast.success("Proposition acceptée");
      await refreshAfterDraftDecision();
    } catch (error) {
      toast.error("Échec de l'acceptation", {
        description: getApiErrorMessage(error),
      });

      if (error instanceof ApiError && error.status === 409) {
        const resolvedFromError =
          parseResolutionFromUnknown(error.bodyJson) ?? parseResolutionFromUnknown(error.detail);

        if (resolvedFromError) {
          setDraftResolution(resolvedFromError);
          setIsAlreadyDecided(false);
        } else {
          setIsAlreadyDecided(true);
        }

        await refreshAfterDraftDecision();
      }
    }
  }, [acceptDraftMutation, draftId, refreshAfterDraftDecision]);

  const handleRejectDraft = React.useCallback(async () => {
    if (!draftId) return;

    try {
      const response = await rejectDraftMutation.trigger();
      const resolved = parseResolutionFromUnknown(response);
      setDraftResolution(resolved);
      setIsAlreadyDecided(resolved === null);
      toast.success("Proposition refusée");
      await refreshAfterDraftDecision();
    } catch (error) {
      toast.error("Échec du refus", {
        description: getApiErrorMessage(error),
      });

      if (error instanceof ApiError && error.status === 409) {
        const resolvedFromError =
          parseResolutionFromUnknown(error.bodyJson) ?? parseResolutionFromUnknown(error.detail);

        if (resolvedFromError) {
          setDraftResolution(resolvedFromError);
          setIsAlreadyDecided(false);
        } else {
          setIsAlreadyDecided(true);
        }

        await refreshAfterDraftDecision();
      }
    }
  }, [draftId, refreshAfterDraftDecision, rejectDraftMutation]);

  React.useEffect(() => {
    if (!jobQuery.error) return;
    toast.error("Impossible de suivre la génération", { description: jobQuery.error.message });
  }, [jobQuery.error]);

  React.useEffect(() => {
    if (!draftQuery.error) return;
    toast.error("Impossible de charger le planning généré", { description: draftQuery.error.message });
  }, [draftQuery.error]);

  React.useEffect(() => {
    if (status !== "failed") return;

    toast.error("La génération a échoué", {
      description: jobQuery.data?.error ?? "Une erreur est survenue côté serveur.",
    });
  }, [jobQuery.data?.error, status]);

  const progress = clampProgress(jobQuery.data?.progress);

  return (
    <>
      <div className="space-y-6 p-4 md:p-6">
        <Card>
          <CardHeader>
            <CardTitle>Génération planning</CardTitle>
            <CardDescription>Choisissez une équipe et une période, puis lancez une proposition automatique.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
              <div className="space-y-2">
                <Label>Équipe</Label>
                <TeamHeaderSelect
                  teams={teamsQuery.data ?? []}
                  valueId={teamId}
                  onChange={setTeamId}
                  disabled={teamsQuery.isLoading || generateMutation.isMutating || isParametersLocked}
                />
              </div>

              <div className="space-y-2">
                <Label>Période</Label>
                <PlanningPeriodControls
                  value={period}
                  onChange={setPeriod}
                  onPrev={() => setPeriod((prev) => shiftPlanningPeriod(prev, -1))}
                  onNext={() => setPeriod((prev) => shiftPlanningPeriod(prev, 1))}
                  disabled={isParametersLocked}
                />
              </div>
            </div>

            {isParametersLocked ? (
              <p className="text-xs text-muted-foreground">Génération en cours — modification des paramètres désactivée.</p>
            ) : null}

            {hasInvalidPeriod ? (
              <Alert variant="destructive">
                <AlertTitle>Période invalide</AlertTitle>
                <AlertDescription>La date de début doit être antérieure ou égale à la date de fin.</AlertDescription>
              </Alert>
            ) : null}

            {hasLongPeriod ? (
              <Alert>
                <AlertTitle>Période longue</AlertTitle>
                <AlertDescription>La période dépasse 31 jours. La génération peut prendre plus de temps.</AlertDescription>
              </Alert>
            ) : null}

            <Button onClick={() => void runGeneration()} disabled={!canGenerate || isParametersLocked}>
              {isJobRunning || generateMutation.isMutating ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Génération en cours…
                </>
              ) : (
                <>
                  <Sparkles className="mr-2 h-4 w-4" />
                  Générer une proposition
                </>
              )}
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>État de génération</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex flex-wrap items-center gap-2">
              {!jobId ? <Badge variant="outline">Idle</Badge> : null}
              {isJobRunning ? <Badge variant="warning">En cours</Badge> : null}
              {status === "success" ? <Badge variant="success">Prêt</Badge> : null}
              {status === "failed" ? <Badge variant="destructive">Échec</Badge> : null}
              {draftId ? <Badge variant="outline">Draft #{draftId}</Badge> : null}
              {draftResolution === "accepted" ? <Badge variant="success">Accepté</Badge> : null}
              {draftResolution === "rejected" ? <Badge variant="warning">Refusé</Badge> : null}
              {isAlreadyDecided ? <Badge variant="outline">Déjà décidé</Badge> : null}
            </div>

            {!jobId ? <p className="text-sm text-muted-foreground">Aucune génération en cours.</p> : null}

            {jobId && isJobRunning ? (
              <div className="space-y-2">
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Génération en cours…
                </div>

                {progress !== null ? (
                  <>
                    <div className="h-2 w-full overflow-hidden rounded-full bg-accent">
                      <div className="h-full bg-primary transition-all" style={{ width: `${Math.round(progress * 100)}%` }} />
                    </div>
                    <p className="text-xs text-muted-foreground">{Math.round(progress * 100)}%</p>
                  </>
                ) : null}
              </div>
            ) : null}

            {lastUpdatedAt ? (
              <p className="text-xs text-muted-foreground">Dernière mise à jour: {format(lastUpdatedAt, "HH:mm:ss")}</p>
            ) : null}

            {status === "success" ? (
              <div className="space-y-2">
                <p className="text-sm text-muted-foreground">La proposition est prête.</p>
                {jobQuery.data?.result_stats ? (
                  <pre className="max-h-44 overflow-auto rounded-md border bg-muted/30 p-3 text-xs">
                    {JSON.stringify(jobQuery.data.result_stats, null, 2)}
                  </pre>
                ) : (
                  <p className="text-xs text-muted-foreground">Aucune statistique de génération disponible.</p>
                )}
              </div>
            ) : null}

            {status === "failed" ? (
              <Alert variant="destructive">
                <AlertTitle>Échec de la génération</AlertTitle>
                <AlertDescription className="space-y-2">
                  <p>La génération n&apos;a pas pu aboutir.</p>
                  {jobQuery.data?.error ? <p className="font-mono text-xs">{jobQuery.data.error}</p> : null}
                  <Button variant="outline" size="sm" onClick={() => void runGeneration()}>
                    Réessayer
                  </Button>
                </AlertDescription>
              </Alert>
            ) : null}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Proposition générée</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="sticky top-14 z-10 rounded-lg border bg-background/95 p-3 backdrop-blur">
              <div className="flex flex-wrap items-center gap-2">
                {canShowDraftActions ? (
                  <>
                    <Button variant="secondary" disabled={actionsLocked} onClick={() => setIsConfirmAcceptOpen(true)}>
                      Accepter
                    </Button>

                    <Button variant="secondary" disabled={actionsLocked} onClick={() => setIsConfirmRejectOpen(true)}>
                      Refuser
                    </Button>
                  </>
                ) : null}

                {canShowDraftActions ? <Separator orientation="vertical" className="hidden h-7 md:block" /> : null}

                <Button onClick={handleGenerateNew} disabled={!teamId || hasInvalidPeriod || isJobRunning || generateMutation.isMutating}>
                  Générer une nouvelle
                </Button>
              </div>
            </div>

            {status === "success" && draftQuery.isLoading ? (
              <div className="space-y-3">
                <Skeleton className="h-10 w-full" />
                <Skeleton className="h-48 w-full" />
              </div>
            ) : null}

            {planningVm ? <TeamPlanningMatrix days={planningVm.days} rows={planningVm.rows} readOnly /> : null}

            {status !== "success" ? (
              <p className="text-sm text-muted-foreground">Lancez une génération pour afficher une proposition de planning.</p>
            ) : null}
          </CardContent>
        </Card>
      </div>

      <AlertDialog open={isConfirmGenerateOpen} onOpenChange={setIsConfirmGenerateOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Générer une nouvelle proposition ?</AlertDialogTitle>
            <AlertDialogDescription>
              La proposition actuelle restera consultable seulement si vous avez son lien job. Continuer ?
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Annuler</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => {
                void runGeneration();
                setIsConfirmGenerateOpen(false);
              }}
            >
              Générer
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      <AlertDialog open={isConfirmAcceptOpen} onOpenChange={setIsConfirmAcceptOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Accepter cette proposition ?</AlertDialogTitle>
            <AlertDialogDescription>Le planning officiel sur cette période sera remplacé.</AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Annuler</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => {
                void handleAcceptDraft();
                setIsConfirmAcceptOpen(false);
              }}
            >
              Accepter
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      <AlertDialog open={isConfirmRejectOpen} onOpenChange={setIsConfirmRejectOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Refuser cette proposition ?</AlertDialogTitle>
            <AlertDialogDescription>La proposition sera marquée comme refusée.</AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Annuler</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => {
                void handleRejectDraft();
                setIsConfirmRejectOpen(false);
              }}
            >
              Refuser
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}
