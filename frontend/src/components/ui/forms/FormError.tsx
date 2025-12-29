"use client";

export default function FormError({ message }: { message?: string | null }) {
  if (!message) return null;
  return (
    <div className="rounded-xl bg-red-50 p-3 text-sm text-red-700 ring-1 ring-red-200">
      {message}
    </div>
  );
}
