"use client";

export default function RequiredFieldsNote({
  text = "Les champs marqués d'un * sont obligatoires.",
}: {
  text?: string;
}) {
  return <div className="text-xs text-zinc-500 italic">{text}</div>;
}
