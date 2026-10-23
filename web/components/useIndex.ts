"use client";

import { useEffect, useState } from "react";
import type { Entry } from "@/lib/types";

let cache: Promise<Entry[]> | null = null;

/** Loads the compact index (one file, or monthly chunks once large) once per page view. */
function loadIndex(): Promise<Entry[]> {
  cache ??= fetch("/data/meta.json")
    .then((r) => r.json() as Promise<{ chunks: string[] }>)
    .then((m) => Promise.all(m.chunks.map((c) => fetch(`/data/${c}`).then((r) => r.json() as Promise<Entry[]>))))
    .then((parts) => parts.flat());
  return cache;
}

export function useIndex(enabled: boolean): Entry[] | null {
  const [entries, setEntries] = useState<Entry[] | null>(null);
  useEffect(() => {
    if (!enabled) return;
    let alive = true;
    loadIndex().then((e) => alive && setEntries(e)).catch(() => alive && setEntries([]));
    return () => {
      alive = false;
    };
  }, [enabled]);
  return entries;
}
