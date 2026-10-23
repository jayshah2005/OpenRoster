"use client";

import { useSyncExternalStore } from "react";

const noop = () => () => {};

/** Shows the start time in the visitor's own zone when it differs from the event's zone (browser only). */
export function LocalTime({ start, tz }: { start: string; tz: string }) {
  const text = useSyncExternalStore(
    noop,
    () => {
      if (Intl.DateTimeFormat().resolvedOptions().timeZone === tz) return "";
      const s = new Intl.DateTimeFormat(undefined, {
        weekday: "short", month: "short", day: "numeric", hour: "numeric", minute: "2-digit", timeZoneName: "short",
      }).format(new Date(start));
      return `Your time: ${s}`;
    },
    () => "",
  );
  return text ? <span className="local-time">{text}</span> : null;
}
