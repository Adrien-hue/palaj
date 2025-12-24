"use client";

export default function ActiveSwitch({
  checked,
  onToggle,
  disabled,
  tooltipOn = "Désactiver",
  tooltipOff = "Activer",
  labelOn = "Actif",
  labelOff = "Inactif",
  showLabel = false,
}: {
  checked: boolean;
  onToggle: () => void;
  disabled?: boolean;
  tooltipOn?: string;
  tooltipOff?: string;
  labelOn?: string;
  labelOff?: string;
  showLabel?: boolean;
}) {
  const tooltip = checked ? tooltipOn : tooltipOff;
  const label = checked ? labelOn : labelOff;

  return (
    <div className="inline-flex items-center gap-2">
      <button
        type="button"
        onClick={onToggle}
        disabled={disabled}
        aria-pressed={checked}
        aria-label={label}
        title={tooltip}
        className={[
          "relative inline-flex h-6 w-11 items-center rounded-full transition",
          checked ? "bg-green-600" : "bg-red-600",
          disabled ? "opacity-60 cursor-not-allowed" : "hover:brightness-110",
          "focus:outline-none focus-visible:ring-2 focus-visible:ring-zinc-400 focus-visible:ring-offset-2",
        ].join(" ")}
      >
        <span
          className={[
            "inline-block h-5 w-5 transform rounded-full bg-white shadow-sm transition",
            checked ? "translate-x-5" : "translate-x-1",
          ].join(" ")}
        />
      </button>

      {showLabel && (
        <span className="text-xs text-zinc-600">
          {label}
        </span>
      )}
    </div>
  );
}
