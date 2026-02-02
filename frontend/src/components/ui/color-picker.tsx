import { useCallback, useEffect, useState } from "react";
import { Label } from "./label";
import { Input } from "./input";
import { Button } from "./button";

const HEX_RE = /^#[0-9A-Fa-f]{6}$/;

function normalizeHex(input: string): string {
  const v = input.trim();
  if (v === "") return "";
  if (v.startsWith("#")) return v.toUpperCase();
  // permet coller "A1B2C3"
  return `#${v}`.toUpperCase();
}

function isValidHex(v: string | null | undefined): boolean {
  if (v == null || v === "") return true;
  return HEX_RE.test(v);
}

export function ColorPicker({
  id,
  label,
  value,
  disabled,
  onChange,
}: {
  id: string;
  label: string;
  value: string | null;
  disabled?: boolean;
  onChange: (next: string | null) => void;
}) {
const [text, setText] = useState<string>(value ?? "");
  useEffect(() => setText(value ?? ""), [value]);

  const valid = isValidHex(text);
  const errorId = `${id}-error`;
  const canReset = text.trim() !== "";

  const commitIfValid = useCallback((raw: string) => {
    const normalized = normalizeHex(raw);
    setText(normalized);

    if (normalized === "") {
      onChange(null);
      return;
    }
    if (HEX_RE.test(normalized)) onChange(normalized);
  }, [onChange]);

  const pickerValue =
    HEX_RE.test(text) ? text : HEX_RE.test(value ?? "") ? (value ?? "") : "#64748B";

  return (
    <div className="grid gap-1.5">
      <Label htmlFor={id}>{label}</Label>

      <div className="flex items-center gap-2">
        <Input
          id={id}
          type="color"
          value={pickerValue}
          onChange={(e) => {
            const v = e.target.value.toUpperCase();
            setText(v);
            onChange(v);
          }}
          disabled={disabled}
          className="h-9 w-12 cursor-pointer p-1"
          aria-label={`${label} (picker)`}
        />

        <Input
          value={text}
          onChange={(e) => setText(normalizeHex(e.target.value))}
          onBlur={(e) => commitIfValid(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") commitIfValid(text);
          }}
          disabled={disabled}
          placeholder="#RRGGBB"
          autoComplete="off"
          className="w-28 font-mono"
          aria-label={`${label} (hex)`}
          aria-describedby={!valid ? errorId : undefined}
        />

        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={() => {
            setText("");
            onChange(null);
          }}
          disabled={disabled || !canReset}
        >
          Réinitialiser
        </Button>
      </div>

      {!valid ? (
        <div id={errorId} className="text-xs text-destructive">
          Couleur invalide. Format attendu : #RRGGBB
        </div>
      ) : null}
    </div>
  );
}