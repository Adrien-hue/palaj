import { listTeams } from "@/services/teams.service";
import { TeamAutoGeneratePage } from "@/features/planning-team-auto-generate/components/TeamAutoGeneratePage";

export default async function TeamAutoGeneratePlanningPage() {
  const teams = await listTeams({ page: 1, page_size: 200 });

  return <TeamAutoGeneratePage teams={teams.items} />;
}
