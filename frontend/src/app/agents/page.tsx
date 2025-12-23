import { apiFetch } from "@/lib/api";
import type { Agent, PaginatedResponse } from "@/lib/types";

export default async function AgentsPage() {
    const response = await apiFetch<PaginatedResponse<Agent>>("/agents");

    const agents = response.items;
    const total = response.total;

    return (
        <main className="p-6">
        <h1 className="text-2xl font-semibold">Agents</h1>

        <div className="mt-4 overflow-x-auto rounded-xl border">
            <table className="min-w-full text-sm">
            <thead className="bg-gray-50">
                <tr>
                <th className="px-4 py-2 text-left">ID</th>
                <th className="px-4 py-2 text-left">Nom</th>
                <th className="px-4 py-2 text-left">Prénom</th>
                <th className="px-4 py-2 text-left">Code</th>
                </tr>
            </thead>
            <tbody>
                {agents.map((a) => (
                <tr key={a.id} className="border-t">
                    <td className="px-4 py-2">{a.id}</td>
                    <td className="px-4 py-2">{a.nom}</td>
                    <td className="px-4 py-2">{a.prenom}</td>
                    <td className="px-4 py-2">{a.code_personnel ?? ""}</td>
                </tr>
                ))}
            </tbody>
            </table>
        </div>
        </main>
    );
}
