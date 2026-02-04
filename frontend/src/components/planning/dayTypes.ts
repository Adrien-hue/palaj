export type DayTypeValue = "working" | "rest" | "absence" | "zcot" | "unknown" | string;

export const DAY_TYPE_OPTIONS: { value: string; label: string }[] = [
  { value: "working", label: "Travail" },
  { value: "rest", label: "Repos" },
  { value: "absent", label: "Absence" },
  { value: "zcot", label: "ZCOT" },
  { value: "leave", label: "Congés" },
  { value: "unknown", label: "Inconnu" },
];

export function dayTypeLabel(value: string) {
  return DAY_TYPE_OPTIONS.find((o) => o.value === value)?.label ?? value;
}
