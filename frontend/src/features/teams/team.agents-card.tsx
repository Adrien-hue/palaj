"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { toast } from "sonner";
import { Plus, Trash2, X } from "lucide-react";

import { useConfirm } from "@/hooks/useConfirm";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";

import type { Team, AgentTeam } from "@/types";
import type { Agent } from "@/types";
import {
  searchAgentTeams,
  addAgentToTeam,
  removeAgentFromTeam,
} from "@/services/agent-teams.service";

import { listAgents } from "@/services/agents.service";

async function fetchAllAgents() {
  const pageSize = 200;
  let page = 1;
  const all: Agent[] = [];

  while (true) {
    const res = await listAgents({ page, page_size: pageSize });
    all.push(...res.items);
    if (res.items.length < pageSize) break;
    page += 1;
  }

  return all;
}

function agentLabel(a: Agent) {
  // adapte si tes champs diffèrent
  const nom = (a as any).nom ?? "";
  const prenom = (a as any).prenom ?? "";
  const label = `${nom} ${prenom}`.trim();
  return label || `Agent #${a.id}`;
}

function isAgent(x: Agent | undefined): x is Agent {
  return x != null;
}

export function TeamAgentsCard({ team }: { team: Team }) {
  const { confirm, ConfirmDialog } = useConfirm();

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [memberships, setMemberships] = useState<AgentTeam[]>([]);
  const [agents, setAgents] = useState<Agent[]>([]);

  const [adding, setAdding] = useState(false);
  const [query, setQuery] = useState("");
  const [selectedAgentId, setSelectedAgentId] = useState<number | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const loadAgents = useCallback(async () => {
    try {
      const all = await fetchAllAgents();
      setAgents(all);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erreur inconnue");
    }
  }, []);

  const loadMemberships = useCallback(async () => {
    try {
      const links = await searchAgentTeams({ team_id: team.id });
      setMemberships(links);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erreur inconnue");
    }
  }, [team.id]);

  useEffect(() => {
    setLoading(true);
    setError(null);

    Promise.all([loadAgents(), loadMemberships()]).finally(() =>
      setLoading(false)
    );
  }, [loadAgents, loadMemberships]);

  const memberAgentIds = useMemo(
    () => new Set(memberships.map((m) => m.agent_id)),
    [memberships]
  );

  const teamAgents = useMemo(() => {
    const map = new Map(agents.map((a) => [a.id, a]));

    return memberships
      .map((m) => map.get(m.agent_id))
      .filter(isAgent)
      .sort((a, b) =>
        agentLabel(a).localeCompare(agentLabel(b), "fr", {
          sensitivity: "base",
        })
      );
  }, [agents, memberships]);

  const candidates = useMemo(() => {
    const q = query.trim().toLowerCase();
    return agents
      .filter((a) => !memberAgentIds.has(a.id))
      .filter((a) => {
        if (!q) return true;
        const label = `${agentLabel(a)} #${a.id}`.toLowerCase();
        return label.includes(q);
      })
      .slice(0, 20);
  }, [agents, memberAgentIds, query]);

  const handleAdd = useCallback(async () => {
    if (!selectedAgentId) return;

    setSubmitting(true);
    try {
      await addAgentToTeam(selectedAgentId, team.id);
      toast.success("Agent ajouté à l’équipe");
      setAdding(false);
      setQuery("");
      setSelectedAgentId(null);
      await loadMemberships();
    } catch (e) {
      toast.error("Ajout impossible", {
        description: e instanceof Error ? e.message : "Erreur inconnue",
      });
    } finally {
      setSubmitting(false);
    }
  }, [selectedAgentId, team.id, loadMemberships]);

  const handleRemove = useCallback(
    async (agent: Agent) => {
      const ok = await confirm({
        title: "Retirer l’agent",
        description: `Confirmer le retrait de "${agentLabel(
          agent
        )}" de l’équipe "${team.name}" ?`,
        confirmText: "Retirer",
        cancelText: "Annuler",
        variant: "danger",
      });
      if (!ok) return;

      setSubmitting(true);
      try {
        await removeAgentFromTeam(agent.id, team.id);
        toast.success("Agent retiré");
        await loadMemberships();
      } catch (e) {
        toast.error("Retrait impossible", {
          description: e instanceof Error ? e.message : "Erreur inconnue",
        });
      } finally {
        setSubmitting(false);
      }
    },
    [confirm, team.id, team.name, loadMemberships]
  );

  return (
    <>
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between gap-3">
            <CardTitle className="text-sm">
              Agents
              <span className="ml-2 text-xs text-muted-foreground">
                {teamAgents.length}
              </span>
            </CardTitle>

            <div className="flex items-center gap-2">
              {!adding ? (
                <Button
                  size="sm"
                  onClick={() => setAdding(true)}
                  disabled={loading || !!error}
                >
                  <Plus className="mr-2 h-4 w-4" />
                  Ajouter
                </Button>
              ) : (
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => {
                    setAdding(false);
                    setQuery("");
                    setSelectedAgentId(null);
                  }}
                  disabled={submitting}
                >
                  <X className="mr-2 h-4 w-4" />
                  Annuler
                </Button>
              )}
            </div>
          </div>
        </CardHeader>

        <CardContent className="space-y-3">
          {adding ? (
            <div className="space-y-2 rounded-xl border bg-muted/30 p-3">
              <div className="text-sm font-medium">Ajouter un agent</div>

              <Input
                value={query}
                onChange={(e) => setQuery(e.currentTarget.value)}
                placeholder="Rechercher un agent…"
                disabled={submitting}
              />

              <div className="max-h-56 overflow-auto rounded-lg border bg-background">
                {candidates.length === 0 ? (
                  <div className="p-3 text-sm text-muted-foreground">
                    Aucun résultat.
                  </div>
                ) : (
                  candidates.map((a) => {
                    const selected = selectedAgentId === a.id;
                    return (
                      <button
                        key={a.id}
                        type="button"
                        className={[
                          "w-full text-left px-3 py-2 text-sm hover:bg-muted",
                          selected ? "bg-muted" : "",
                        ].join(" ")}
                        onClick={() => setSelectedAgentId(a.id)}
                        disabled={submitting}
                      >
                        <div className="font-medium truncate">
                          {agentLabel(a)}
                        </div>
                        <div className="text-xs text-muted-foreground truncate">
                          #{a.id}
                        </div>
                      </button>
                    );
                  })
                )}
              </div>

              <div className="flex justify-end">
                <Button
                  onClick={handleAdd}
                  disabled={!selectedAgentId || submitting}
                >
                  Ajouter à l’équipe
                </Button>
              </div>
            </div>
          ) : null}

          {loading ? (
            <div className="space-y-2">
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
            </div>
          ) : error ? (
            <div className="text-sm text-destructive">{error}</div>
          ) : teamAgents.length === 0 ? (
            <div className="text-sm text-muted-foreground">
              Aucun agent associé à cette équipe.
              <br />
              Utilise le bouton <strong>Ajouter</strong> pour en associer un.
            </div>
          ) : (
            <div className="space-y-2">
              {teamAgents.map((a) => (
                <div
                  key={a.id}
                  className="flex items-center justify-between gap-3 rounded-lg border bg-muted/40 px-3 py-2"
                >
                  <div className="min-w-0">
                    <div className="truncate text-sm font-medium">
                      {agentLabel(a)}
                    </div>
                    <div className="text-xs text-muted-foreground">#{a.id}</div>
                  </div>

                  <Button
                    variant="ghost"
                    size="icon"
                    aria-label="Retirer"
                    onClick={() => void handleRemove(a)}
                    disabled={submitting}
                  >
                    <Trash2 className="h-4 w-4 text-destructive" />
                  </Button>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      <ConfirmDialog />
    </>
  );
}
