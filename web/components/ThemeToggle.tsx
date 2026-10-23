"use client";

/** Flips between light and dark, starting from whatever is showing now (saved choice or system setting). */
export function ThemeToggle() {
  function toggle() {
    const root = document.documentElement;
    const current = root.dataset.theme ?? (matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
    const next = current === "dark" ? "light" : "dark";
    root.dataset.theme = next;
    try {
      localStorage.setItem("or-theme", next);
    } catch {
      // storage can be unavailable (private mode); the toggle still works for this page
    }
  }

  return (
    <button type="button" className="theme-toggle" onClick={toggle} aria-label="Toggle dark mode" title="Toggle dark mode">
      <span aria-hidden="true">◐</span>
    </button>
  );
}
