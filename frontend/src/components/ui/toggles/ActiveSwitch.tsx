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
          checked
            ? "bg-[color:var(--app-switch-on)]"
            : "bg-[color:var(--app-switch-off)]",
          disabled
            ? "cursor-not-allowed opacity-60"
            : "cursor-pointer active:scale-[0.98] hover:ring-1 hover:ring-[color:var(--app-ring)] hover:ring-inset",
          "focus:outline-none",
          "focus-visible:ring-2 focus-visible:ring-[color:var(--app-focus)]",
          "focus-visible:ring-offset-2 focus-visible:ring-offset-[color:var(--app-focus-offset)]",
        ].join(" ")}
      >
        <span
          className={[
            "inline-block h-5 w-5 transform rounded-full transition",
            "bg-[color:var(--app-switch-knob)]",
            "shadow-[0_1px_2px_var(--app-switch-knob-shadow)]",
            checked ? "translate-x-5" : "translate-x-1",
          ].join(" ")}
        />
      </button>

      {showLabel && (
        <span className="text-xs text-[color:var(--app-label)]">{label}</span>
      )}
    </div>
  );
}
