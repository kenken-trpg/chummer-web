"use client";

import { useState } from "react";

export function SpecPicker({
  options,
  value,
  disabled,
  emptyLabel = "専門なし",
  placeholder = "専門化",
  tr,
  onDraft,
  onCommit,
}: {
  options: string[];
  value: string;
  disabled?: boolean;
  emptyLabel?: string;
  placeholder?: string;
  tr: (name: string) => string;
  onDraft: (next: string) => void;
  onCommit: (next: string) => void;
}) {
  const [customMode, setCustomMode] = useState(() => Boolean(value && !options.includes(value)));
  const selectValue =
    !value && !customMode
      ? ""
      : customMode || (value && !options.includes(value))
        ? "__custom__"
        : value;
  return (
    <span className="spec-pick">
      <select
        disabled={disabled}
        value={selectValue}
        title={value ? tr(value) : emptyLabel}
        onChange={(e) => {
          const next = e.target.value;
          if (next === "__custom__") {
            setCustomMode(true);
            return;
          }
          setCustomMode(false);
          onCommit(next);
        }}
      >
        <option value="">{emptyLabel}</option>
        {options.map((spec) => (
          <option key={spec} value={spec}>
            {tr(spec)}
          </option>
        ))}
        <option value="__custom__">自由入力</option>
      </select>
      {(customMode || (value && !options.includes(value))) && !disabled ? (
        <input
          value={value}
          placeholder={placeholder}
          onChange={(e) => onDraft(e.target.value)}
          onBlur={(e) => onCommit(e.target.value.trim())}
        />
      ) : null}
    </span>
  );
}
