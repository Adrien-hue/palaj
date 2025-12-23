import { listRegimes } from "@/services";

export default async function RegimesPage() {
  const { items: regimes, meta } = await listRegimes({ page: 1, page_size: 25 });

  return (
    <main className="p-6">
      <div className="flex items-end justify-between gap-4">
        <h1 className="text-2xl font-semibold">
          Régimes <span className="text-gray-500">({meta.total})</span>
        </h1>

        <p className="text-sm text-gray-600">
          Page {meta.page} / {meta.pages} — {meta.page_size} par page
        </p>
      </div>

      <div className="mt-4 overflow-x-auto rounded-xl border">
        <table className="min-w-full text-sm">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-2 text-left">ID</th>
              <th className="px-4 py-2 text-left">Nom</th>
              <th className="px-4 py-2 text-left">Description</th>
            </tr>
          </thead>
          <tbody>
            {regimes.map((p) => (
              <tr key={p.id} className="border-t">
                <td className="px-4 py-2">{p.id}</td>
                <td className="px-4 py-2">{p.nom}</td>
                <td className="px-4 py-2">{p.desc}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </main>
  );
}
