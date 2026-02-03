import { listTeams } from "@/services/teams.service";
import { monthAnchorISO } from "@/features/planning-common/utils/month.utils";
import { TeamPlanningClient } from "@/features/planning-team/components/TeamPlanningClient";

type PageProps = {
  searchParams: Promise<{ date?: string; anchor?: string }>;
};

export default async function TeamsPlanningPage({ searchParams }: PageProps) {
  const sp = await searchParams;

  const [teamsList] = await Promise.all([listTeams()]);

  const todayISO = new Date().toISOString().slice(0, 10);
  const initialAnchor = monthAnchorISO(sp.anchor ?? sp.date ?? todayISO);

  return (
    <TeamPlanningClient
      initialTeamId={null}
      initialAnchor={initialAnchor}
      teams={teamsList.items}
    />
  );
}
