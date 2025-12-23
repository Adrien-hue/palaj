import { Loading } from "@/components/Loading";

export default function AgentsLoading() {
  return (
    <main className="p-6">
      <h1 className="text-2xl font-semibold">Agents</h1>
      <Loading label="Chargement des agents..." />
    </main>
  );
}
