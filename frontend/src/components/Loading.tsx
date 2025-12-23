export function Loading({ label = "Chargement..." }: { label?: string }) {
  return (
    <div className="flex items-center gap-3 py-10">
      <div className="h-5 w-5 animate-spin rounded-full border-2 border-gray-300 border-t-gray-900" />
      <p className="text-sm text-gray-600">{label}</p>
    </div>
  );
}