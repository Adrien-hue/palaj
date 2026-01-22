import { listPostes } from "@/services";
import type { ListParams } from "@/types";

import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { PostePicker } from "@/components/postes/PostePicker";

export default async function PlanningPostesIndexPage() {
  const params: ListParams = { page: 1, page_size: 200 };
  const data = await listPostes(params);

  return (
    <div className="mx-auto max-w-2xl">
      <Card className="border-[color:var(--app-border)] bg-[color:var(--app-surface)] shadow-sm">
        <CardHeader className="space-y-2">
          <h1 className="text-2xl font-semibold tracking-tight text-[color:var(--app-text)]">
            Planning par poste
          </h1>
          <p className="text-sm text-[color:var(--app-muted)]">
            Choisis un poste pour ouvrir son planning.
          </p>
        </CardHeader>
        <CardContent className="pt-0">
          <PostePicker postes={data.items} />
        </CardContent>
      </Card>
    </div>
  );
}
