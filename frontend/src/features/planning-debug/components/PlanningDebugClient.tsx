"use client";

import * as React from "react";
import { endOfMonth, format, startOfMonth } from "date-fns";
import { Loader2, RefreshCw } from "lucide-react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { toast } from "sonner";

import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { Switch } from "@/components/ui/switch";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { PlanningPeriodControls } from "@/features/planning-common/period/PlanningPeriodControls";
import type { PlanningPeriod } from "@/features/planning-common/period/period.types";
import { shiftPlanningPeriod } from "@/features/planning-common/period/period.utils";
import { useTeams } from "@/features/planning-generation/hooks/useTeams";
import { TeamHeaderSelect } from "@/features/planning-team/components/TeamHeaderSelect";
import { TeamPlanningMatrix } from "@/features/planning-team/components/TeamPlanningMatrix";
import { buildTeamPlanningVm } from "@/features/planning-team/vm/teamPlanning.vm.builder";
import { toISODate } from "@/utils/date.format";

import { DEFAULT_DEBUG_GENERATE_PARAMS, type DebugGenerateParams } from "../constants";
import { usePlanningDebugDraftPlanning } from "../hooks/usePlanningDebugDraftPlanning";
import { usePlanningDebugGenerate } from "../hooks/usePlanningDebugGenerate";
import { usePlanningDebugJob } from "../hooks/usePlanningDebugJob";
import { usePlanningDebugJobs } from "../hooks/usePlanningDebugJobs";

const QUALITY_PROFILE_OPTIONS = ["fast", "balanced", "quality"] as const;
const V3_STRATEGY_OPTIONS = ["two_phase_lns", "phase1_only", "phase2_only"] as const;
const LNS_MODE_OPTIONS = ["top_days_global", "top_days_per_agent", "random"] as const;

type NumberField =
  | "seed"
  | "time_limit_seconds"
  | "phase1_fraction"
  | "lns_iter_seconds"
  | "min_lns_seconds"
  | "lns_min_remaining_seconds"
  | "lns_max_days_to_relax"
  | "phase2_max_fraction_of_remaining"
  | "phase2_no_improve_seconds";

type ParamsDraft = Omit<DebugGenerateParams, NumberField> & Record<NumberField, string>;

function toDraft(defaults: DebugGenerateParams): ParamsDraft {
  return {
    ...defaults,
    seed: String(defaults.seed),
    time_limit_seconds: String(defaults.time_limit_seconds),
    phase1_fraction: String(defaults.phase1_fraction),
    lns_iter_seconds: String(defaults.lns_iter_seconds),
    min_lns_seconds: String(defaults.min_lns_seconds),
    lns_min_remaining_seconds: String(defaults.lns_min_remaining_seconds),
    lns_max_days_to_relax: String(defaults.lns_max_days_to_relax),
    phase2_max_fraction_of_remaining: String(defaults.phase2_max_fraction_of_remaining),
    phase2_no_improve_seconds: String(defaults.phase2_no_improve_seconds),
  };
}

function getRecord(value: unknown): Record<string, unknown> | null {
  if (!value || typeof value !== "object") return null;
  return value as Record<string, unknown>;
}

function getPath(source: unknown, path: string[]): unknown {
  let current: unknown = source;
  for (const key of path) {
    const record = getRecord(current);
    if (!record || !(key in record)) return undefined;
    current = record[key];
  }
  return current;
}

function formatUnknown(value: unknown) {
  if (value === undefined || value === null || value === "") return "—";
  if (typeof value === "number") return Number.isFinite(value) ? String(value) : "—";
  if (typeof value === "boolean") return value ? "true" : "false";
  if (typeof value === "string") return value;
  return JSON.stringify(value);
}

function shortId(jobId: string) {
  if (jobId.length <= 12) return jobId;
  return `${jobId.slice(0, 6)}…${jobId.slice(-4)}`;
}

function extractStats(payload: unknown) {
  const stats = getPath(payload, ["result_stats", "stats"]);
  return getRecord(stats) ?? {};
}

function validateParams(draft: ParamsDraft): { errors: string[]; parsed: DebugGenerateParams | null } {
  const errors: string[] = [];
  const parseNum = (value: string, label: string) => {
    if (value.trim() === "") {
      errors.push(`${label}: valeur requise.`);
      return null;
    }
    const parsed = Number(value);
    if (!Number.isFinite(parsed)) {
      errors.push(`${label}: nombre invalide.`);
      return null;
    }
    return parsed;
  };

  const seed = parseNum(draft.seed, "seed");
  const timeLimit = parseNum(draft.time_limit_seconds, "time_limit_seconds");
  const phase1Fraction = parseNum(draft.phase1_fraction, "phase1_fraction");
  const lnsIter = parseNum(draft.lns_iter_seconds, "lns_iter_seconds");
  const minLns = parseNum(draft.min_lns_seconds, "min_lns_seconds");
  const minRemaining = parseNum(draft.lns_min_remaining_seconds, "lns_min_remaining_seconds");
  const maxRelax = parseNum(draft.lns_max_days_to_relax, "lns_max_days_to_relax");
  const phase2MaxFraction = parseNum(draft.phase2_max_fraction_of_remaining, "phase2_max_fraction_of_remaining");
  const phase2NoImprove = parseNum(draft.phase2_no_improve_seconds, "phase2_no_improve_seconds");

  const nonNegative: Array<[number | null, string]> = [
    [seed, "seed"],
    [timeLimit, "time_limit_seconds"],
    [lnsIter, "lns_iter_seconds"],
    [minLns, "min_lns_seconds"],
    [minRemaining, "lns_min_remaining_seconds"],
    [maxRelax, "lns_max_days_to_relax"],
    [phase2NoImprove, "phase2_no_improve_seconds"],
  ];

  nonNegative.forEach(([value, key]) => {
    if (value !== null && value < 0) errors.push(`${key} doit être >= 0.`);
  });

  if (phase1Fraction !== null && (phase1Fraction < 0 || phase1Fraction > 1)) {
    errors.push("phase1_fraction doit être entre 0 et 1.");
  }

  if (phase2MaxFraction !== null && (phase2MaxFraction <= 0 || phase2MaxFraction > 1)) {
    errors.push("phase2_max_fraction_of_remaining doit être > 0 et <= 1.");
  }

  if (errors.length > 0) return { errors, parsed: null };

  return {
    errors,
    parsed: {
      seed: seed!,
      time_limit_seconds: timeLimit!,
      quality_profile: draft.quality_profile,
      v3_strategy: draft.v3_strategy,
      phase1_fraction: phase1Fraction!,
      lns_neighborhood_mode: draft.lns_neighborhood_mode,
      lns_iter_seconds: lnsIter!,
      min_lns_seconds: minLns!,
      lns_min_remaining_seconds: minRemaining!,
      lns_strict_improve: draft.lns_strict_improve,
      lns_max_days_to_relax: maxRelax!,
      phase2_max_fraction_of_remaining: phase2MaxFraction!,
      phase2_no_improve_seconds: phase2NoImprove!,
      enable_decision_strategy: draft.enable_decision_strategy,
      enable_symmetry_breaking: draft.enable_symmetry_breaking,
    },
  };
}

export function PlanningDebugClient() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  const teamsQuery = useTeams();
  const [teamId, setTeamId] = React.useState<number | null>(null);
  const [searchJob, setSearchJob] = React.useState("");
  const [statusFilter, setStatusFilter] = React.useState<string>("all");
  const [selectedJobFromList, setSelectedJobFromList] = React.useState<string>("none");
  const [jobId, setJobId] = React.useState<string | null>(null);
  const [autoRefresh, setAutoRefresh] = React.useState(true);
  const [paramsDraft, setParamsDraft] = React.useState<ParamsDraft>(toDraft(DEFAULT_DEBUG_GENERATE_PARAMS));

  const [period, setPeriod] = React.useState<PlanningPeriod>({ kind: "month", month: startOfMonth(new Date()) });

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

  const validation = React.useMemo(() => validateParams(paramsDraft), [paramsDraft]);

  const updateJobInUrl = React.useCallback(
    (nextJobId: string | null) => {
      const params = new URLSearchParams(searchParams.toString());
      if (nextJobId) params.set("job", nextJobId);
      else params.delete("job");
      const query = params.toString();
      router.replace(query ? `${pathname}?${query}` : pathname, { scroll: false });
    },
    [pathname, router, searchParams],
  );

  React.useEffect(() => {
    const queryJob = searchParams.get("job");
    if (!queryJob) return;
    setJobId((prev) => (prev === queryJob ? prev : queryJob));
    setSelectedJobFromList(queryJob);
  }, [searchParams]);

  const jobsQuery = usePlanningDebugJobs({
    q: searchJob || undefined,
    status: statusFilter === "all" ? undefined : statusFilter,
    team_id: teamId ?? undefined,
  });

  const generateMutation = usePlanningDebugGenerate();
  const jobQuery = usePlanningDebugJob(jobId, autoRefresh);
  const currentJobId = jobQuery.data?.job_id ?? null;
  const hasCurrentJobData = Boolean(jobId && currentJobId === jobId);

  const safeDraftId =
    hasCurrentJobData && typeof jobQuery.data?.draft_id === "number" && jobQuery.data.draft_id > 0
      ? jobQuery.data.draft_id
      : null;

  const draftQuery = usePlanningDebugDraftPlanning(safeDraftId);

  const planningVm = React.useMemo(() => {
    if (!safeDraftId || !draftQuery.data) return null;
    return buildTeamPlanningVm(draftQuery.data);
  }, [draftQuery.data, safeDraftId]);

  const stats = React.useMemo(() => (hasCurrentJobData ? extractStats(jobQuery.data) : {}), [hasCurrentJobData, jobQuery.data]);
  const status = hasCurrentJobData ? jobQuery.data?.status : undefined;
  const isRunning = status === "queued" || status === "running";

  const canGenerate =
    teamId !== null &&
    range.startDate <= range.endDate &&
    !generateMutation.isMutating &&
    validation.errors.length === 0 &&
    validation.parsed !== null;

  const loadJob = React.useCallback(
    (nextJobId: string) => {
      setJobId(nextJobId);
      setSelectedJobFromList(nextJobId);
      updateJobInUrl(nextJobId);
    },
    [updateJobInUrl],
  );

  const handleLoadJob = React.useCallback(() => {
    if (!selectedJobFromList || selectedJobFromList === "none") return;
    loadJob(selectedJobFromList);
  }, [loadJob, selectedJobFromList]);

  const handleRunGenerate = React.useCallback(async () => {
    if (!canGenerate || teamId === null || !validation.parsed) return;

    try {
      const response = await generateMutation.trigger({
        team_id: teamId,
        start_date: range.startDate,
        end_date: range.endDate,
        ...validation.parsed,
      });

      loadJob(response.job_id);
      toast.success("Génération debug lancée", { description: `Job ${response.job_id}` });
    } catch (error) {
      toast.error("Impossible de lancer la génération debug", {
        description: error instanceof Error ? error.message : "Erreur inconnue",
      });
    }
  }, [canGenerate, generateMutation, loadJob, range.endDate, range.startDate, teamId, validation.parsed]);

  const handleRefresh = React.useCallback(async () => {
    await Promise.all([jobQuery.mutate(), jobsQuery.mutate()]);
  }, [jobQuery, jobsQuery]);

  const summaryItems: Array<{ label: string; value: unknown }> = [
    { label: "status", value: status },
    { label: "progress", value: hasCurrentJobData ? jobQuery.data?.progress : undefined },
    { label: "job_id", value: hasCurrentJobData ? jobQuery.data?.job_id : jobId },
    { label: "draft_id", value: safeDraftId },
    { label: "solver_version", value: getPath(jobQuery.data, ["solver_version"]) ?? getPath(stats, ["solver_version"]) },
    { label: "verbosity", value: getPath(jobQuery.data, ["verbosity"]) ?? getPath(stats, ["verbosity"]) },
    { label: "time_limit_seconds", value: getPath(jobQuery.data, ["time_limit_seconds"]) ?? getPath(stats, ["time_limit_seconds"]) },
    { label: "solve_wall_time_seconds", value: getPath(jobQuery.data, ["solve_wall_time_seconds"]) ?? getPath(stats, ["solve_wall_time_seconds"]) },
    { label: "model_build_wall_time_seconds", value: getPath(jobQuery.data, ["model_build_wall_time_seconds"]) ?? getPath(stats, ["model_build_wall_time_seconds"]) },
    { label: "coverage_ratio", value: getPath(stats, ["coverage_ratio"]) },
    { label: "coverage_ratio_weighted", value: getPath(stats, ["coverage_ratio_weighted"]) },
    { label: "objective_value / score", value: getPath(stats, ["objective_value"]) ?? getPath(stats, ["score"]) },
    { label: "phase1_normalized_status", value: getPath(stats, ["phase1_normalized_status"]) },
    { label: "phase2_normalized_status", value: getPath(stats, ["phase2_normalized_status"]) },
    { label: "lns_enabled", value: getPath(stats, ["lns_enabled"]) },
    { label: "lns_iterations", value: getPath(stats, ["lns_iterations"]) },
    { label: "lns_accept_count_total", value: getPath(stats, ["lns_accept_count_total"]) },
    { label: "time_to_first_feasible_seconds", value: getPath(stats, ["time_to_first_feasible_seconds"]) },
    { label: "error", value: hasCurrentJobData ? jobQuery.data?.error : undefined },
  ];

  const topUnderstaffDays = getPath(stats, ["top_understaff_days"]);
  const understaffByDay = getPath(stats, ["understaff_by_day_weighted"]);
  const iterationHistory = getPath(stats, ["iteration_history"]);
  const cpSatParams = getPath(stats, ["cp_sat_params_effective"]);
  const phases = getPath(stats, ["phases"]);
  const jobOptions = jobsQuery.data ?? [];

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Debug Solver</CardTitle>
          <CardDescription>Suivi temps réel des jobs de génération et analyse solver.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-5">
          <div className="flex flex-wrap items-end gap-3">
            <div className="min-w-[320px]">
              <Label>Équipe</Label>
              <TeamHeaderSelect teams={teamsQuery.data ?? []} valueId={teamId} onChange={setTeamId} disabled={generateMutation.isMutating} />
            </div>
            <PlanningPeriodControls
              value={period}
              onChange={setPeriod}
              onPrev={() => setPeriod((prev) => shiftPlanningPeriod(prev, -1))}
              onNext={() => setPeriod((prev) => shiftPlanningPeriod(prev, +1))}
            />
          </div>

          <div className="grid gap-3 md:grid-cols-[1fr_180px_260px_auto_auto_auto]">
            <div>
              <Label htmlFor="job-search">Recherche job</Label>
              <Input id="job-search" value={searchJob} onChange={(e) => setSearchJob(e.currentTarget.value)} placeholder="job_id..." />
            </div>
            <div>
              <Label>Status</Label>
              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Tous</SelectItem>
                  <SelectItem value="queued">queued</SelectItem>
                  <SelectItem value="running">running</SelectItem>
                  <SelectItem value="success">success</SelectItem>
                  <SelectItem value="failed">failed</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>Job existant</Label>
              <Select value={selectedJobFromList} onValueChange={setSelectedJobFromList}>
                <SelectTrigger>
                  <SelectValue placeholder="Choisir un job" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="none">Aucun</SelectItem>
                  {jobOptions.map((job) => (
                    <SelectItem key={job.job_id} value={job.job_id}>
                      {`${job.team_name ?? "Team ?"} • ${job.start_date ?? "?"}→${job.end_date ?? "?"} • ${job.status} • ${shortId(job.job_id)} • ${job.created_at ? format(new Date(job.created_at), "dd/MM HH:mm") : "?"}`}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <Button variant="outline" onClick={handleLoadJob} disabled={selectedJobFromList === "none"}>
              Charger le job
            </Button>
            <Button variant="outline" onClick={() => void handleRefresh()}>
              <RefreshCw className="mr-2 h-4 w-4" />Rafraîchir
            </Button>
            <div className="flex items-center gap-2 pt-6">
              <Switch id="auto-refresh" checked={autoRefresh} onCheckedChange={setAutoRefresh} />
              <Label htmlFor="auto-refresh">Auto-refresh</Label>
            </div>
          </div>

          <Accordion type="single" collapsible>
            <AccordionItem value="advanced">
              <AccordionTrigger>Paramètres solver avancés</AccordionTrigger>
              <AccordionContent>
                <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
                  <div>
                    <Label htmlFor="seed">Seed</Label>
                    <Input id="seed" value={paramsDraft.seed} type="number" min={0} onChange={(e) => setParamsDraft((p) => ({ ...p, seed: e.currentTarget.value }))} />
                  </div>
                  <div>
                    <Label htmlFor="time_limit_seconds">Time limit (s)</Label>
                    <Input id="time_limit_seconds" value={paramsDraft.time_limit_seconds} type="number" min={0} onChange={(e) => setParamsDraft((p) => ({ ...p, time_limit_seconds: e.currentTarget.value }))} />
                  </div>
                  <div>
                    <Label>Quality profile</Label>
                    <Select
                      value={paramsDraft.quality_profile}
                      onValueChange={(value: (typeof QUALITY_PROFILE_OPTIONS)[number]) => setParamsDraft((p) => ({ ...p, quality_profile: value }))}
                    >
                      <SelectTrigger><SelectValue /></SelectTrigger>
                      <SelectContent>
                        {QUALITY_PROFILE_OPTIONS.map((option) => <SelectItem key={option} value={option}>{option}</SelectItem>)}
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label>V3 strategy</Label>
                    <Select
                      value={paramsDraft.v3_strategy}
                      onValueChange={(value: (typeof V3_STRATEGY_OPTIONS)[number]) => setParamsDraft((p) => ({ ...p, v3_strategy: value }))}
                    >
                      <SelectTrigger><SelectValue /></SelectTrigger>
                      <SelectContent>
                        {V3_STRATEGY_OPTIONS.map((option) => <SelectItem key={option} value={option}>{option}</SelectItem>)}
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label htmlFor="phase1_fraction">Phase 1 fraction</Label>
                    <Input id="phase1_fraction" value={paramsDraft.phase1_fraction} type="number" min={0} max={1} step="any" onChange={(e) => setParamsDraft((p) => ({ ...p, phase1_fraction: e.currentTarget.value }))} />
                  </div>
                  <div>
                    <Label>LNS neighborhood mode</Label>
                    <Select
                      value={paramsDraft.lns_neighborhood_mode}
                      onValueChange={(value: (typeof LNS_MODE_OPTIONS)[number]) => setParamsDraft((p) => ({ ...p, lns_neighborhood_mode: value }))}
                    >
                      <SelectTrigger><SelectValue /></SelectTrigger>
                      <SelectContent>
                        {LNS_MODE_OPTIONS.map((option) => <SelectItem key={option} value={option}>{option}</SelectItem>)}
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label htmlFor="lns_iter_seconds">LNS iter seconds</Label>
                    <Input id="lns_iter_seconds" value={paramsDraft.lns_iter_seconds} type="number" min={0} step="any" onChange={(e) => setParamsDraft((p) => ({ ...p, lns_iter_seconds: e.currentTarget.value }))} />
                  </div>
                  <div>
                    <Label htmlFor="min_lns_seconds">Min LNS seconds</Label>
                    <Input id="min_lns_seconds" value={paramsDraft.min_lns_seconds} type="number" min={0} step="any" onChange={(e) => setParamsDraft((p) => ({ ...p, min_lns_seconds: e.currentTarget.value }))} />
                  </div>
                  <div>
                    <Label htmlFor="lns_min_remaining_seconds">LNS min remaining seconds</Label>
                    <Input id="lns_min_remaining_seconds" value={paramsDraft.lns_min_remaining_seconds} type="number" min={0} step="any" onChange={(e) => setParamsDraft((p) => ({ ...p, lns_min_remaining_seconds: e.currentTarget.value }))} />
                  </div>
                  <div>
                    <Label htmlFor="lns_max_days_to_relax">LNS max days to relax</Label>
                    <Input id="lns_max_days_to_relax" value={paramsDraft.lns_max_days_to_relax} type="number" min={0} onChange={(e) => setParamsDraft((p) => ({ ...p, lns_max_days_to_relax: e.currentTarget.value }))} />
                  </div>
                  <div>
                    <Label htmlFor="phase2_max_fraction_of_remaining">Phase2 max fraction</Label>
                    <Input id="phase2_max_fraction_of_remaining" value={paramsDraft.phase2_max_fraction_of_remaining} type="number" min={0.0001} max={1} step="any" onChange={(e) => setParamsDraft((p) => ({ ...p, phase2_max_fraction_of_remaining: e.currentTarget.value }))} />
                  </div>
                  <div>
                    <Label htmlFor="phase2_no_improve_seconds">Phase2 no improve seconds</Label>
                    <Input id="phase2_no_improve_seconds" value={paramsDraft.phase2_no_improve_seconds} type="number" min={0} step="any" onChange={(e) => setParamsDraft((p) => ({ ...p, phase2_no_improve_seconds: e.currentTarget.value }))} />
                  </div>

                  <div className="flex items-center justify-between rounded-md border p-3">
                    <Label htmlFor="lns_strict_improve">LNS strict improve</Label>
                    <Switch id="lns_strict_improve" checked={paramsDraft.lns_strict_improve} onCheckedChange={(checked) => setParamsDraft((p) => ({ ...p, lns_strict_improve: checked }))} />
                  </div>
                  <div className="flex items-center justify-between rounded-md border p-3">
                    <Label htmlFor="enable_decision_strategy">Decision strategy</Label>
                    <Switch id="enable_decision_strategy" checked={paramsDraft.enable_decision_strategy} onCheckedChange={(checked) => setParamsDraft((p) => ({ ...p, enable_decision_strategy: checked }))} />
                  </div>
                  <div className="flex items-center justify-between rounded-md border p-3">
                    <Label htmlFor="enable_symmetry_breaking">Symmetry breaking</Label>
                    <Switch id="enable_symmetry_breaking" checked={paramsDraft.enable_symmetry_breaking} onCheckedChange={(checked) => setParamsDraft((p) => ({ ...p, enable_symmetry_breaking: checked }))} />
                  </div>
                </div>

                {validation.errors.length > 0 ? (
                  <Alert variant="destructive" className="mt-3">
                    <AlertTitle>Paramètres invalides</AlertTitle>
                    <AlertDescription>{validation.errors[0]}</AlertDescription>
                  </Alert>
                ) : null}
              </AccordionContent>
            </AccordionItem>
          </Accordion>

          <Button onClick={() => void handleRunGenerate()} disabled={!canGenerate}>
            {generateMutation.isMutating ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
            Lancer une génération debug
          </Button>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Résumé technique</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-2 sm:grid-cols-2 xl:grid-cols-4">
          {summaryItems.map((item) => (
            <div key={item.label} className="rounded-md border p-3">
              <p className="text-xs text-muted-foreground">{item.label}</p>
              <p className="text-sm font-medium break-all">{formatUnknown(item.value)}</p>
            </div>
          ))}
        </CardContent>
      </Card>

      <Tabs defaultValue="summary" className="space-y-4">
        <TabsList>
          <TabsTrigger value="summary">Résumé</TabsTrigger>
          <TabsTrigger value="planning">Planning</TabsTrigger>
          <TabsTrigger value="coverage">Coverage</TabsTrigger>
          <TabsTrigger value="lns">LNS</TabsTrigger>
          <TabsTrigger value="cpsat">CP-SAT</TabsTrigger>
          <TabsTrigger value="raw">Raw JSON</TabsTrigger>
        </TabsList>

        <TabsContent value="summary" className="space-y-4">
          {!jobId ? <Alert><AlertTitle>Aucune sélection</AlertTitle><AlertDescription>Sélectionnez ou lancez un job.</AlertDescription></Alert> : null}
          {jobId && !hasCurrentJobData && jobQuery.isLoading ? <Skeleton className="h-32 w-full" /> : null}
          {status === "failed" ? <Alert variant="destructive"><AlertTitle>Job failed</AlertTitle><AlertDescription>{jobQuery.data?.error ?? "Erreur inconnue"}</AlertDescription></Alert> : null}
          {status === "success" && !jobQuery.data?.result_stats ? (
            <Alert><AlertTitle>Aucune stats</AlertTitle><AlertDescription>result_stats absent pour ce job.</AlertDescription></Alert>
          ) : null}

          <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
            {Object.entries({
              meta: getPath(jobQuery.data, ["result_stats", "meta"]),
              timing: getPath(stats, ["timing"]),
              objective: getPath(stats, ["objective"]),
              solution_quality: getPath(stats, ["solution_quality"]),
            }).map(([key, value]) => (
              <Card key={key}>
                <CardHeader className="py-3"><CardTitle className="text-sm">{key}</CardTitle></CardHeader>
                <CardContent>
                  <pre className="max-h-40 overflow-auto rounded-md bg-muted p-2 text-xs">{JSON.stringify(value ?? {}, null, 2)}</pre>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="planning">
          {!safeDraftId ? (
            <Alert><AlertTitle>Aucun draft</AlertTitle><AlertDescription>Le job n&apos;a pas encore de draft exploitable.</AlertDescription></Alert>
          ) : null}
          {safeDraftId && draftQuery.isLoading ? <Skeleton className="h-60 w-full" /> : null}
          {planningVm ? <TeamPlanningMatrix days={planningVm.days} rows={planningVm.rows} readOnly /> : null}
        </TabsContent>

        <TabsContent value="coverage" className="space-y-3">
          <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
            {[
              ["coverage_ratio", getPath(stats, ["coverage_ratio"])],
              ["coverage_ratio_weighted", getPath(stats, ["coverage_ratio_weighted"])],
              ["understaff_total", getPath(stats, ["understaff_total"])],
              ["understaff_total_weighted", getPath(stats, ["understaff_total_weighted"])],
            ].map(([k, v]) => (
              <Card key={String(k)}><CardContent className="pt-4"><p className="text-xs text-muted-foreground">{String(k)}</p><p className="text-lg font-semibold">{formatUnknown(v)}</p></CardContent></Card>
            ))}
          </div>

          <Card>
            <CardHeader><CardTitle className="text-sm">Top understaff days</CardTitle></CardHeader>
            <CardContent>
              <pre className="max-h-56 overflow-auto rounded-md bg-muted p-2 text-xs">{JSON.stringify(topUnderstaffDays ?? [], null, 2)}</pre>
            </CardContent>
          </Card>

          <Card>
            <CardHeader><CardTitle className="text-sm">Understaff by day weighted</CardTitle></CardHeader>
            <CardContent>
              <pre className="max-h-56 overflow-auto rounded-md bg-muted p-2 text-xs">{JSON.stringify(understaffByDay ?? {}, null, 2)}</pre>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="lns" className="space-y-3">
          <div className="grid gap-3 md:grid-cols-3">
            {["lns_enabled", "lns_iterations", "lns_accept_count_total", "lns_best_improvement_objective", "lns_fallback_triggered", "lns_early_stop_triggered"].map((k) => (
              <Card key={k}><CardContent className="pt-4"><p className="text-xs text-muted-foreground">{k}</p><p>{formatUnknown(getPath(stats, [k]))}</p></CardContent></Card>
            ))}
          </div>

          <Accordion type="single" collapsible>
            <AccordionItem value="iteration-history">
              <AccordionTrigger>Iteration history (compact)</AccordionTrigger>
              <AccordionContent>
                <Table>
                  <TableHeader>
                    <TableRow><TableHead>#</TableHead><TableHead>Value</TableHead></TableRow>
                  </TableHeader>
                  <TableBody>
                    {(Array.isArray(iterationHistory) ? iterationHistory.slice(-25) : []).map((item, index) => (
                      <TableRow key={index}><TableCell>{index + 1}</TableCell><TableCell className="max-w-[500px] truncate">{formatUnknown(item)}</TableCell></TableRow>
                    ))}
                  </TableBody>
                </Table>
                <p className="mt-2 text-xs text-muted-foreground">Total: {Array.isArray(iterationHistory) ? iterationHistory.length : 0} (affichage des 25 dernières lignes)</p>
              </AccordionContent>
            </AccordionItem>
          </Accordion>
        </TabsContent>

        <TabsContent value="cpsat" className="space-y-3">
          <div className="grid gap-3 md:grid-cols-3">
            {[
              ["phase1", getPath(cpSatParams, ["phase1"])],
              ["phase2", getPath(cpSatParams, ["phase2"])],
              ["lns", getPath(cpSatParams, ["lns"])],
              ["decision_strategy_enabled", getPath(stats, ["decision_strategy_enabled"])],
              ["symmetry_breaking_enabled", getPath(stats, ["symmetry_breaking_enabled"])],
              ["phases.phase1", getPath(phases, ["phase1"])],
              ["phases.phase2", getPath(phases, ["phase2"])],
            ].map(([k, v]) => (
              <Card key={String(k)}><CardHeader className="py-3"><CardTitle className="text-sm">{String(k)}</CardTitle></CardHeader><CardContent><pre className="max-h-40 overflow-auto rounded-md bg-muted p-2 text-xs">{JSON.stringify(v ?? {}, null, 2)}</pre></CardContent></Card>
            ))}
          </div>

          <Card>
            <CardHeader><CardTitle className="text-sm">best_objective_over_time_points</CardTitle></CardHeader>
            <CardContent><pre className="max-h-56 overflow-auto rounded-md bg-muted p-2 text-xs">{JSON.stringify(getPath(stats, ["best_objective_over_time_points"]) ?? [], null, 2)}</pre></CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="raw">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle>Raw JSON</CardTitle>
              <Button
                variant="outline"
                size="sm"
                onClick={async () => {
                  const pretty = JSON.stringify(jobQuery.data ?? {}, null, 2);
                  try {
                    if (typeof navigator === "undefined" || !navigator.clipboard?.writeText) {
                      throw new Error("Clipboard API indisponible");
                    }
                    await navigator.clipboard.writeText(pretty);
                    toast.success("JSON copié");
                  } catch (error) {
                    toast.error("Impossible de copier", {
                      description: error instanceof Error ? error.message : "Erreur inconnue",
                    });
                  }
                }}
              >
                Copier
              </Button>
            </CardHeader>
            <CardContent>
              <pre className="max-h-[600px] overflow-auto rounded-md bg-muted p-3 text-xs">{JSON.stringify(jobQuery.data ?? {}, null, 2)}</pre>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <Badge variant={isRunning ? "default" : "secondary"}>{status ?? "idle"}</Badge>
        {jobQuery.isValidating ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
        {isRunning ? <span>Job running...</span> : null}
      </div>
    </div>
  );
}
