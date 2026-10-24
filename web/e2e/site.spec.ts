import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";

const ids = async (page: import("@playwright/test").Page) =>
  page.locator(".cards .card-title a").evaluateAll((as) => as.map((a) => (a as HTMLAnchorElement).pathname));

test("a filtered URL reproduces the same view in a fresh browser (AC4)", async ({ browser }) => {
  const url = "/?type=hackathon&mode=in_person";
  const a = await (await browser.newContext()).newPage();
  await a.goto(url);
  await expect(a.locator(".result-count")).toContainText("match");
  const first = await ids(a);
  expect(first.length).toBeGreaterThan(0);

  const b = await (await browser.newContext({ viewport: { width: 390, height: 844 }, isMobile: true })).newPage();
  await b.goto(url);
  await expect(b.locator(".result-count")).toContainText("match");
  expect(await ids(b)).toEqual(first);
});

test("changing a filter updates the URL", async ({ page }) => {
  await page.goto("/");
  const type = page.getByRole("combobox", { name: "Type" });
  await type.fill("hack");
  await expect(page.getByRole("option", { name: "Hackathon" })).toBeVisible();
  await type.press("Enter");
  await expect(page).toHaveURL(/type=hackathon/);
  await expect(page.locator(".result-count")).toContainText("match");
  await expect(type).toHaveValue("Hackathon");
});

test("dropdowns can be picked with the mouse and cleared", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("combobox", { name: "I want to" }).click();
  await page.getByRole("option", { name: "volunteer" }).click();
  await expect(page).toHaveURL(/role=volunteer/);
  await page.getByRole("combobox", { name: "I want to" }).click();
  await page.getByRole("option", { name: "do anything" }).click();
  await expect(page).not.toHaveURL(/role=/);
});

test("the digest and programs pages have filters", async ({ page }) => {
  await page.goto("/digest/");
  await expect(page.getByRole("search", { name: "Filter opportunities" })).toBeVisible();
  await page.goto("/programs/");
  const total = await page.locator(".programs .card").count();
  expect(total).toBeGreaterThan(0);
  await page.getByRole("combobox", { name: "My year" }).fill("first");
  await page.getByRole("combobox", { name: "My year" }).press("Enter");
  const firstYear = await page.locator(".programs .card").count();
  expect(firstYear).toBeGreaterThan(0);
  expect(firstYear).toBeLessThan(total);
});

test("the list works without JavaScript", async ({ browser }) => {
  const page = await (await browser.newContext({ javaScriptEnabled: false })).newPage();
  await page.goto("/");
  expect(await page.locator(".cards .card").count()).toBeGreaterThan(0);
  await expect(page.getByText("Filters need JavaScript")).toBeVisible();
  await page.goto("/calendar/");
  expect(await page.locator(".agenda-list li").count()).toBeGreaterThan(0);
});

test("filtered views offer a matching feed", async ({ page, request }) => {
  await page.goto("/?type=hackathon");
  // Wait for the filtered results; until then the server-rendered list (with the all.ics link) is showing.
  await expect(page.locator(".result-count")).toContainText("match");
  const href = await page.getByRole("link", { name: "Calendar (.ics)" }).getAttribute("href");
  expect(href).toContain("/api/feed.ics?type=hackathon");
  const res = await request.get(href!);
  expect(res.headers()["content-type"]).toContain("text/calendar");
  expect(await res.text()).toContain("BEGIN:VCALENDAR");
});

for (const path of ["/", "/calendar/", "/about/", "/start/", "/programs/", "/contribute/", "/data/"]) {
  for (const scheme of ["light", "dark"] as const) {
    test(`no serious accessibility problems on ${path} (${scheme})`, async ({ browser }) => {
      const page = await (await browser.newContext({ colorScheme: scheme })).newPage();
      await page.goto(path);
      const results = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa"]).analyze();
      const serious = results.violations.filter((v) => v.impact === "serious" || v.impact === "critical");
      expect(serious.map((v) => `${v.id}: ${v.nodes[0]?.target}`)).toEqual([]);
    });
  }
}
