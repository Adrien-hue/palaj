"use client";

import * as React from "react";
import { endOfMonth, startOfMonth } from "date-fns";
import { Loader2 } from "lucide-react";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";

import { ApiError } from "@/lib/api/errors";
import type { Team } from "@/types";
import { toISODate } from "@/utils/date.format";
import { PlanningPeriodControls } from "@/features/planning-common/period/PlanningPeriodControls";
import type { PlanningPeriod } from "@/features/planning-common/period/period.types";
import { shiftPlanningPeriod } from "@/features/planning-common/period/period.utils";
import { TeamHeaderSelect } from "@/features/planning-team/components/TeamHeaderSelect";
import { TeamPlanningMatrix } from "@/features/planning-team/components/TeamPlanningMatrix";
import { buildTeamPlanningVm } from "@/features/planning-team/vm/teamPlanning.vm.builder";

import { DebugStatsCard } from "./DebugStatsCard";
import { usePlanningGenerateHistory } from "../hooks/usePlanningGenerateHistory";
import {
  useTeamPlanningGenerate,
  type JobStatus,
  type PlanningGenerateRequest,
} from "../hooks/useTeamPlanningGenerate";
import { useTeamPlanningDraft } from "../hooks/useTeamPlanningDraft";
import { useTeamPlanningGenerateJob } from "../hooks/useTeamPlanningGenerateJob";

const statusLabels: Record<JobStatus, string> = {
  queued: "queued",
  running: "running",
  success: "success",
  failed: "failed",
};

type SelectionMode = "job" | "draft";

function statusVariant(status: JobStatus): "secondary" | "default" | "success" | "destructive" {
  if (status === "queued") return "secondary";
  if (status === "running") return "default";
  if (status === "success") return "success";
  return "destructive";
}

function formatErrorMessage(error: unknown) {
  if (!error) return "Erreur inconnue";
  if (typeof error === "string") return error;
  return JSON.stringify(error);
}

export function TeamAutoGeneratePage({ teams }: { teams: Team[] }) {
  const [teamId, setTeamId] = React.useState<number | null>(null);
  const [seed, setSeed] = React.useState(0);
  const [timeLimitSeconds, setTimeLimitSeconds] = React.useState(60);

  const [period, setPeriod] = React.useState<PlanningPeriod>({
    kind: "month",
    month: startOfMonth(new Date()),
  });

  const [jobId, setJobId] = React.useState<string | null>(null);
  const [draftId, setDraftId] = React.useState<number | null>(null);
  const [selectionMode, setSelectionMode] = React.useState<SelectionMode>("job");
  const [showConflictAlert, setShowConflictAlert] = React.useState(false);
  const [draftNotFound, setDraftNotFound] = React.useState(false);
  const [isSubmittingLocal, setIsSubmittingLocal] = React.useState(false);

  const submitTokenRef = React.useRef(0);

  const {
    history,
    lastJobId,
    setLastJobId,
    upsertFromGenerateResponse,
    updateStatus,
    select,
    selectDraft,
  } = usePlanningGenerateHistory();

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

  const generate = useTeamPlanningGenerate();
  const job = useTeamPlanningGenerateJob(jobId);
  const draft = useTeamPlanningDraft(draftId);

  const isPeriodInvalid = range.startDate > range.endDate;
  const isRunning = job.data?.status === "queued" || job.data?.status === "running";
  const isBusy = generate.isSubmitting || isSubmittingLocal || isRunning;
  const canGenerate = teamId !== null && !isPeriodInvalid && !isBusy;

  React.useEffect(() => {
    if (jobId || !lastJobId) return;
    setJobId(lastJobId);
    setSelectionMode("job");
  }, [jobId, lastJobId]);

  React.useEffect(() => {
    if (!jobId || !job.data) return;

    updateStatus(jobId, job.data.status, job.data.draft_id);

    if (job.data.status === "success" && job.data.draft_id) {
      setDraftId(job.data.draft_id);
      setDraftNotFound(false);
      setSelectionMode("job");
    }
  }, [jobId, job.data, updateStatus]);

  React.useEffect(() => {
    if (!draft.error) {
      setDraftNotFound(false);
      return;
    }

    if (draft.error instanceof ApiError && draft.error.status === 404) {
      setDraftNotFound(true);
      return;
    }

    setDraftNotFound(false);
  }, [draft.error]);

  const planningVm = React.useMemo(() => {
    if (!draft.data) return null;
    return buildTeamPlanningVm(draft.data);
  }, [draft.data]);

  const resetViewState = React.useCallback(() => {
    setShowConflictAlert(false);
    setDraftNotFound(false);
  }, []);

  const clearSWRLocalViews = React.useCallback(async () => {
    await Promise.all([job.clearJobCache(), draft.clearDraftCache()]);
  }, [job, draft]);

  const handleGenerate = React.useCallback(async () => {
    if (!canGenerate || teamId === null || isSubmittingLocal) return;

    setIsSubmittingLocal(true);
    resetViewState();

    const submitToken = submitTokenRef.current + 1;
    submitTokenRef.current = submitToken;

    const payload: PlanningGenerateRequest = {
      team_id: teamId,
      start_date: range.startDate,
      end_date: range.endDate,
      seed,
      time_limit_seconds: timeLimitSeconds,
    };

    try {
      const response = await generate.submit(payload);
      if (submitToken !== submitTokenRef.current) return;

      setJobId(response.job_id);
      setSelectionMode("job");
      setLastJobId(response.job_id);
      setDraftId(response.draft_id ?? null);
      upsertFromGenerateResponse(response, payload);
    } catch (error) {
      if (submitToken !== submitTokenRef.current) return;

      if (error instanceof ApiError && error.status === 409) {
        setShowConflictAlert(true);

        if (jobId) {
          setLastJobId(jobId);
          await job.mutate();
          return;
        }

        if (lastJobId) {
          setJobId(lastJobId);
          setSelectionMode("job");
          await job.mutate();
        }
      }
    } finally {
      if (submitToken === submitTokenRef.current) {
        setIsSubmittingLocal(false);
      }
    }
  }, [
    canGenerate,
    teamId,
    isSubmittingLocal,
    resetViewState,
    range.startDate,
    range.endDate,
    seed,
    timeLimitSeconds,
    generate,
    setLastJobId,
    upsertFromGenerateResponse,
    jobId,
    lastJobId,
    job,
  ]);

  const onSelectJob = React.useCallback(
    async (value: string) => {
      resetViewState();
      setSelectionMode("job");
      setDraftId(null);
      await clearSWRLocalViews();

      setJobId(value);
      setLastJobId(value);

      const selected = select(value);
      if (selected?.draft_id) {
        setDraftId(selected.draft_id);
      }
    },
    [resetViewState, clearSWRLocalViews, setLastJobId, select],
  );

  const onSelectDraft = React.useCallback(
    async (value: string) => {
      resetViewState();
      setSelectionMode("draft");
      setJobId(null);
      await clearSWRLocalViews();

      const parsedDraft = Number(value);
      setDraftId(parsedDraft);

      const item = selectDraft(parsedDraft);
      if (item?.job_id) setLastJobId(item.job_id);
    },
    [resetViewState, clearSWRLocalViews, selectDraft, setLastJobId],
  );

  const clearSelection = React.useCallback(async () => {
    setJobId(null);
    setDraftId(null);
    setSelectionMode("job");
    resetViewState();
    await clearSWRLocalViews();
  }, [resetViewState, clearSWRLocalViews]);

  return (
    <div className="space-y-6 p-4 md:p-6">
      <Card>
        <CardHeader>
          <CardTitle>Génération automatique de planning équipe</CardTitle>
          <CardDescription>Lance une génération asynchrone, suit le job puis affiche le draft généré.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
            <div className="space-y-2">
              <Label>Équipe</Label>
              <TeamHeaderSelect teams={teams} valueId={teamId} onChange={setTeamId} />
            </div>

            <div className="space-y-2">
              <Label>Période</Label>
              <PlanningPeriodControls
                value={period}
                onChange={setPeriod}
                onPrev={() => setPeriod((p) => shiftPlanningPeriod(p, -1))}
                onNext={() => setPeriod((p) => shiftPlanningPeriod(p, 1))}
              />
            </div>
          </div>

          <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="seed">Seed</Label>
              <Input id="seed" type="number" value={seed} onChange={(e) => setSeed(Number(e.target.value))} />
            </div>

            <div className="space-y-2">
              <Label htmlFor="time-limit">Time limit (secondes)</Label>
              <Input
                id="time-limit"
                type="number"
                min={1}
                value={timeLimitSeconds}
                onChange={(e) => setTimeLimitSeconds(Number(e.target.value))}
              />
            </div>
          </div>

          {isPeriodInvalid ? (
            <Alert variant="destructive">
              <AlertTitle>Période invalide</AlertTitle>
              <AlertDescription>La date de début doit être antérieure ou égale à la date de fin.</AlertDescription>
            </Alert>
          ) : null}

          <div className="space-y-2">
            <Button onClick={handleGenerate} disabled={!canGenerate}>
              {isBusy ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  génération en cours
                </>
              ) : (
                "Lancer génération"
              )}
            </Button>

            {!canGenerate ? (
              <p className="text-xs text-muted-foreground">
                {teamId === null
                  ? "Sélectionnez une équipe pour lancer la génération."
                  : isPeriodInvalid
                    ? "Corrigez la période avant de lancer la génération."
                    : "Une génération est déjà en cours (queued/running)."}
              </p>
            ) : null}
          </div>

          {showConflictAlert ? (
            <Alert>
              <AlertTitle>Une génération est déjà en cours.</AlertTitle>
              <AlertDescription>
                {jobId || lastJobId
                  ? "Reprise du polling sur le job connu."
                  : "Aucun job connu. Sélectionnez un job récent dans l’historique si vous ne connaissez pas le job en cours."}
              </AlertDescription>
            </Alert>
          ) : null}

          {generate.error && !(generate.error instanceof ApiError && generate.error.status === 409) ? (
            <Alert variant="destructive">
              <AlertTitle>Erreur génération</AlertTitle>
              <AlertDescription>{generate.error.message}</AlertDescription>
            </Alert>
          ) : null}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Historique dev/debug</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <Label>Recharger un job</Label>
              <Select value={jobId ?? undefined} onValueChange={(value) => void onSelectJob(value)}>
                <SelectTrigger>
                  <SelectValue placeholder="Sélectionner un job_id" />
                </SelectTrigger>
                <SelectContent>
                  {history.map((item) => (
                    <SelectItem key={item.job_id} value={item.job_id}>
                      {item.job_id} ({item.status_last_known})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label>Afficher un draft</Label>
              <Select value={draftId ? String(draftId) : undefined} onValueChange={(value) => void onSelectDraft(value)}>
                <SelectTrigger>
                  <SelectValue placeholder="Sélectionner un draft_id" />
                </SelectTrigger>
                <SelectContent>
                  {history
                    .filter((item) => item.draft_id)
                    .map((item) => (
                      <SelectItem key={`${item.job_id}-${item.draft_id}`} value={String(item.draft_id)}>
                        Draft #{item.draft_id} (job {item.job_id.slice(0, 8)}…)
                      </SelectItem>
                    ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" onClick={() => void clearSelection()}>
              Réinitialiser
            </Button>
            {jobId ? (
              <Button variant="outline" size="sm" onClick={() => void job.mutate()}>
                Rafraîchir statut
              </Button>
            ) : null}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Statut du job</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <p className="text-xs text-muted-foreground">
            Mode: {selectionMode === "job" ? "Job actif" : "Draft sélectionné"}
          </p>
          {jobId ? <p className="text-xs text-muted-foreground">job_id: {jobId}</p> : null}

          {job.data?.status ? (
            <div className="flex items-center gap-2">
              <Badge variant={statusVariant(job.data.status)}>{statusLabels[job.data.status]}</Badge>
              {job.data.status === "queued" || job.data.status === "running" ? (
                <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
              ) : null}
            </div>
          ) : null}

          {job.data?.status === "failed" ? (
            <Alert variant="destructive">
              <AlertTitle>La génération a échoué</AlertTitle>
              <AlertDescription className="space-y-2">
                <p>{formatErrorMessage(job.data.error)}</p>
                {job.data.solver_status ? <p>solver_status: {job.data.solver_status}</p> : null}
                {job.data.result_stats ? (
                  <ScrollArea className="h-28 rounded-md border bg-muted/30 p-2">
                    <pre className="text-xs">{JSON.stringify(job.data.result_stats, null, 2)}</pre>
                  </ScrollArea>
                ) : null}
              </AlertDescription>
            </Alert>
          ) : null}

          {job.error ? (
            <Alert variant="destructive">
              <AlertTitle>Erreur statut job</AlertTitle>
              <AlertDescription>{job.error.message}</AlertDescription>
            </Alert>
          ) : null}
        </CardContent>
      </Card>

      <DebugStatsCard data={job.data} />

      <Separator />

      {draftNotFound ? (
        <Alert variant="destructive">
          <AlertTitle>Draft introuvable (supprimé / non créé)</AlertTitle>
          <AlertDescription className="space-y-3">
            <p>Le planning du draft n&apos;est pas disponible.</p>
            <Button variant="outline" size="sm" onClick={() => void job.mutate()}>
              Recharger statut du job
            </Button>
          </AlertDescription>
        </Alert>
      ) : null}

      <Card>
        <CardHeader>
          <CardTitle>Planning du draft</CardTitle>
        </CardHeader>
        <CardContent>
          {!draftId ? (
            <p className="text-sm text-muted-foreground">Aucun draft sélectionné.</p>
          ) : draft.isLoading ? (
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Loader2 className="h-4 w-4 animate-spin" />
              Chargement du planning draft…
            </div>
          ) : planningVm ? (
            <TeamPlanningMatrix days={planningVm.days} rows={planningVm.rows} readOnly />
          ) : (
            <p className="text-sm text-muted-foreground">Aucune donnée de planning à afficher.</p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
