import { listPostes } from "@/services";
import type { ListParams } from "@/types";

import { monthAnchorISO } from "@/features/planning-common/utils/month.utils";
import { PostePlanningClient } from "@/features/planning-poste/components/PostePlanningClient";

type PageProps = {
  searchParams: Promise<{ anchor?: string; date?: string }>;
};

export default async function PlanningPostesPage({ searchParams }: PageProps) {
  const sp = await searchParams;

  const params: ListParams = { page: 1, page_size: 200 };
  const data = await listPostes(params);

  const todayISO = new Date().toISOString().slice(0, 10);
  const initialAnchor = monthAnchorISO(sp.anchor ?? sp.date ?? todayISO);

  return (
    <PostePlanningClient
      initialPosteId={null}
      initialAnchor={initialAnchor}
      postes={data.items}
    />
  );
}
