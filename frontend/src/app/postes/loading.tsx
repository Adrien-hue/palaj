import { Loading } from "@/components/Loading";

export default function PostesLoading() {
  return (
    <main className="p-6">
      <h1 className="text-2xl font-semibold">Postes</h1>
      <Loading label="Chargement des postes..." />
    </main>
  );
}
