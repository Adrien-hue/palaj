"use client";

export function ErrorState({
  title = "Une erreur est survenue",
  message,
  onRetry,
}: {
  title?: string;
  message?: string;
  onRetry?: () => void;
}) {
  return (
    <div className="py-10">
      <h2 className="text-lg font-semibold">{title}</h2>
      {message ? <p className="mt-2 text-sm text-gray-600">{message}</p> : null}

      {onRetry ? (
        <button
          type="button"
          onClick={onRetry}
          className="mt-4 rounded-lg border px-3 py-2 text-sm hover:bg-gray-50"
        >
          Réessayer
        </button>
      ) : null}
    </div>
  );
}
