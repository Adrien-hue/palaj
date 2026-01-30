import { useEffect, useMemo, useRef, useState } from "react";

type Params = {
  allDates: string[];
  selectedDate: string | null;
  setSelectedDate: (d: string | null) => void;

  isDisabled: (date: string) => boolean;
  closeOnEscape: boolean;
};

export type FocusBindings = {
  tabIndex: number;
  ref: (el: HTMLDivElement | null) => void;
  onFocus: () => void;
  onKeyDown: (e: React.KeyboardEvent) => void;
};

export function useRovingGridFocus({
  allDates,
  selectedDate,
  setSelectedDate,
  isDisabled,
  closeOnEscape,
}: Params) {
  const cellRefs = useRef<Map<string, HTMLDivElement>>(new Map());
  const lastFocusedElRef = useRef<HTMLElement | null>(null);

  const firstFocusableDate = useMemo(() => {
    for (const d of allDates) {
      if (!isDisabled(d)) return d;
    }
    return null;
  }, [allDates, isDisabled]);

  const [focusedDate, setFocusedDate] = useState<string | null>(null);

  // Initialize focus target
  useEffect(() => {
    if (focusedDate) return;
    if (selectedDate && !isDisabled(selectedDate)) {
      setFocusedDate(selectedDate);
      return;
    }
    if (firstFocusableDate) setFocusedDate(firstFocusableDate);
  }, [firstFocusableDate, focusedDate, selectedDate, isDisabled]);

  // Keep focused date valid when range changes
  useEffect(() => {
    if (!focusedDate) return;
    const inGrid = focusedDate >= allDates[0] && focusedDate <= allDates[allDates.length - 1];
    if (!inGrid || isDisabled(focusedDate)) setFocusedDate(firstFocusableDate);
  }, [allDates, focusedDate, firstFocusableDate, isDisabled]);

  const focusDate = (date: string) => {
    setFocusedDate(date);
    const el = cellRefs.current.get(date);
    if (el) requestAnimationFrame(() => el.focus());
  };

  const moveFocus = (from: string, deltaDays: number) => {
    const i = allDates.indexOf(from);
    if (i < 0) return;

    let j = i + deltaDays;
    if (j < 0) j = 0;
    if (j >= allDates.length) j = allDates.length - 1;

    const step = deltaDays === 0 ? 0 : deltaDays > 0 ? 1 : -1;
    while (j >= 0 && j < allDates.length) {
      const target = allDates[j];
      if (!isDisabled(target)) return focusDate(target);
      if (step === 0) return;
      j += step;
    }
  };

  const rememberActiveElement = () => {
    lastFocusedElRef.current = document.activeElement as HTMLElement | null;
  };

  const restoreRememberedFocus = () => {
    const el = lastFocusedElRef.current;
    if (!el) return;
    requestAnimationFrame(() => el.focus?.());
  };

  // Escape closes selection
  useEffect(() => {
    if (!closeOnEscape) return;
    if (!selectedDate) return;

    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") setSelectedDate(null);
    };

    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [closeOnEscape, selectedDate, setSelectedDate]);

  // When selection closes (drawer closes), restore focus to last focused cell/wrapper
  useEffect(() => {
    if (selectedDate) return;
    restoreRememberedFocus();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedDate]);

  const getFocusBindings = (date: string): FocusBindings => {
    const disabled = isDisabled(date);
    const tabIndex = focusedDate === date && !disabled ? 0 : -1;

    return {
      tabIndex,
      ref: (el) => {
        if (!el) {
          cellRefs.current.delete(date);
          return;
        }
        cellRefs.current.set(date, el);
      },
      onFocus: () => setFocusedDate(date),
      onKeyDown: (e) => {
        if (e.key === "ArrowLeft") {
          e.preventDefault();
          moveFocus(date, -1);
          return;
        }
        if (e.key === "ArrowRight") {
          e.preventDefault();
          moveFocus(date, +1);
          return;
        }
        if (e.key === "ArrowUp") {
          e.preventDefault();
          moveFocus(date, -7);
          return;
        }
        if (e.key === "ArrowDown") {
          e.preventDefault();
          moveFocus(date, +7);
          return;
        }
        if (e.key === "Home") {
          e.preventDefault();
          if (firstFocusableDate) focusDate(firstFocusableDate);
          return;
        }
        if (e.key === "End") {
          e.preventDefault();
          for (let k = allDates.length - 1; k >= 0; k--) {
            const d = allDates[k];
            if (!isDisabled(d)) {
              focusDate(d);
              break;
            }
          }
          return;
        }
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          if (disabled) return;
          setFocusedDate(date);
          rememberActiveElement();
          setSelectedDate(date);
        }
      },
    };
  };

  return {
    focusedDate,
    setFocusedDate,
    focusDate,
    rememberActiveElement,
    getFocusBindings,
  };
}
