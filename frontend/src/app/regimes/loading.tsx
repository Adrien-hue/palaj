import { Loading } from "@/components/Loading";

export default function RegimesLoading() {
  return (
    <main className="p-6">
      <h1 className="text-2xl font-semibold">Régimes</h1>
      <Loading label="Chargement des régimes..." />
    </main>
  );
}
