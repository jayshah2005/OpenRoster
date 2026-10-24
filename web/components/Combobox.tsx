"use client";

import { type KeyboardEvent, useId, useRef, useState } from "react";

type Props = {
  label: string;
  name: string;
  value: string;
  options: [value: string, label: string][];
  /** Shown when nothing is picked, and offered first in the list to clear the choice. */
  anyLabel: string;
  onChange: (value: string) => void;
  disabled?: boolean;
};

/**
 * A dropdown you can type into: typing narrows the options, arrow keys move, Enter picks, Escape closes.
 * Follows the WAI-ARIA combobox pattern so screen readers announce it like a select.
 */
export function Combobox({ label, name, value, options, anyLabel, onChange, disabled }: Props) {
  const id = useId();
  const listId = `${id}-list`;
  const current = options.find(([v]) => v === value)?.[1] ?? "";
  const [open, setOpen] = useState(false);
  const [text, setText] = useState<string | null>(null); // null: not typing, show the picked label
  const [active, setActive] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);

  const query = (text ?? "").trim().toLowerCase();
  const shown: [string, string][] = [
    ["", anyLabel],
    ...options.filter(([, l]) => !query || l.toLowerCase().includes(query)),
  ];

  function pick(v: string) {
    setOpen(false);
    setText(null);
    if (v !== value) onChange(v);
  }

  function onKeyDown(ev: KeyboardEvent<HTMLInputElement>) {
    if (ev.key === "ArrowDown" || ev.key === "ArrowUp") {
      ev.preventDefault();
      if (!open) return setOpen(true);
      const step = ev.key === "ArrowDown" ? 1 : -1;
      setActive((a) => (a + step + shown.length) % shown.length);
    } else if (ev.key === "Enter") {
      if (!open) return;
      ev.preventDefault();
      // With a typed query, Enter takes the first real match rather than "any".
      const target = shown[active === 0 && query && shown.length > 1 ? 1 : active];
      if (target) pick(target[0]);
    } else if (ev.key === "Escape") {
      setOpen(false);
      setText(null);
    }
  }

  return (
    <div className="combo" data-open={open || undefined}>
      <label htmlFor={id}>{label}</label>
      <div className="combo-field">
        <input
          ref={inputRef}
          id={id}
          name={name}
          type="text"
          role="combobox"
          aria-expanded={open}
          aria-controls={listId}
          aria-autocomplete="list"
          aria-activedescendant={open ? `${id}-${active}` : undefined}
          autoComplete="off"
          disabled={disabled}
          placeholder={anyLabel}
          value={text ?? current}
          onFocus={(ev) => {
            ev.target.select();
            setActive(0);
            setOpen(true);
          }}
          onClick={() => setOpen(true)}
          onChange={(ev) => {
            setText(ev.target.value);
            setActive(0);
            setOpen(true);
          }}
          onBlur={() => {
            // Typing an exact label and tabbing away counts as picking it; clearing the box clears the filter.
            if (text !== null) {
              const exact = options.find(([, l]) => l.toLowerCase() === query);
              if (exact) onChange(exact[0]);
              else if (!query && value) onChange("");
            }
            setOpen(false);
            setText(null);
          }}
          onKeyDown={onKeyDown}
        />
        <svg className="combo-caret" width="16" height="16" viewBox="0 0 24 24" aria-hidden="true">
          <path d="m6 9 6 6 6-6" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
        </svg>
      </div>
      {open && (
        <ul className="combo-list" id={listId} role="listbox" aria-label={label}>
          {shown.map(([v, l], i) => (
            <li
              key={v || "__any"}
              id={`${id}-${i}`}
              role="option"
              aria-selected={v === value}
              data-active={i === active || undefined}
              // mousedown, not click: picking must happen before the input's blur closes the list
              onMouseDown={(ev) => {
                ev.preventDefault();
                pick(v);
              }}
              onMouseEnter={() => setActive(i)}
            >
              {l}
            </li>
          ))}
          {shown.length === 1 && query && <li className="combo-none" role="option" aria-selected={false} aria-disabled="true">No matches</li>}
        </ul>
      )}
    </div>
  );
}
