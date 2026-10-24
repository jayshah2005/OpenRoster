import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";

const ids = async (page: import("@playwright/test").Page) =>
  page.locator(".cards .card-title a").evaluateAll((as) => as.map((a) => (a as HTMLAnchorElement).pathname));

test("a filtered URL reproduces the same view in a fresh browser (AC4)", async ({ browser }) => {
  const url = "/?type=hackathon&mode=in_person";
  const a = await (await browser.newContext()).newPage();
  await a.goto(url);
  await expect(a.locator(".result-count")).toContainText("result");
  const first = await ids(a);
  expect(first.length).toBeGreaterThan(0);

  const b = await (await browser.newContext({ viewport: { width: 390, height: 844 }, isMobile: true })).newPage();
  await b.goto(url);
  await expect(b.locator(".result-count")).toContainText("result");
  expect(await ids(b)).toEqual(first);
});

test("ticking a filter updates the URL and the counts", async ({ page }) => {
  await page.goto("/");
  const hack = page.getByRole("checkbox", { name: /^Hackathons/ });
  await hack.check();
  await expect(page).toHaveURL(/type=hackathon/);
  await expect(page.locator(".result-count")).toContainText("result");
  const shown = await page.locator(".cards .card").count();
  expect(shown).toBeGreaterThan(0);
  expect(await page.locator(".cards .card-program").count()).toBe(0);
  await hack.uncheck();
  await expect(page).not.toHaveURL(/type=/);
});

test("typeable dropdowns pick with the keyboard or the mouse", async ({ page }) => {
  await page.goto("/");
  const year = page.getByRole("combobox", { name: "My year of study" });
  await year.fill("thi");
  await expect(page.getByRole("option", { name: "Third year" })).toBeVisible();
  await year.press("Enter");
  await expect(page).toHaveURL(/year=3/);
  await expect(year).toHaveValue("Third year");
  await year.click();
  await page.getByRole("option", { name: "any year" }).click();
  await expect(page).not.toHaveURL(/year=/);
});

test("filters are remembered for the next visit, but a shared link wins", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("checkbox", { name: /^Hackathons/ }).check();
  await expect(page).toHaveURL(/type=hackathon/);
  await page.goto("/");
  await expect(page).toHaveURL(/type=hackathon/);
  await expect(page.getByText("Showing your saved filters")).toBeVisible();
  // Opening someone's link shows their view but keeps our saved filters.
  await page.goto("/?type=workshop");
  await expect(page).toHaveURL(/type=workshop$/);
  await page.goto("/");
  await expect(page).toHaveURL(/type=hackathon/);
  await page.getByRole("button", { name: "Clear all" }).click();
  await expect(page).not.toHaveURL(/\?/);
  await page.goto("/");
  await expect(page.locator(".result-count")).toContainText("result");
  await expect(page).not.toHaveURL(/\?/);
});

test("events and recurring programs share one list", async ({ page }) => {
  await page.goto("/");
  await expect(page.locator(".result-count")).toContainText("result");
  expect(await page.locator(".cards .card-program").count()).toBeGreaterThan(0);
  await page.goto("/programs/");
  await expect(page.locator(".result-count")).toContainText("result");
  const total = await page.locator(".cards .card-program").count();
  await page.getByRole("combobox", { name: "My year of study" }).fill("first");
  await page.getByRole("combobox", { name: "My year of study" }).press("Enter");
  await expect(page).toHaveURL(/year=1/);
  const firstYear = await page.locator(".cards .card-program").count();
  expect(firstYear).toBeGreaterThan(0);
  expect(firstYear).toBeLessThan(total);
});

test("on a phone the filters fold into a button", async ({ browser }) => {
  const page = await (await browser.newContext({ viewport: { width: 390, height: 844 }, isMobile: true })).newPage();
  await page.goto("/digest/");
  const toggle = page.getByRole("button", { name: /^Filters/ });
  await expect(toggle).toBeVisible();
  await expect(page.getByRole("combobox", { name: "My year of study" })).toBeHidden();
  await toggle.click();
  await expect(page.getByRole("combobox", { name: "My year of study" })).toBeVisible();
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
  await expect(page.locator(".result-count")).toContainText("result");
  const href = await page.getByRole("link", { name: "Calendar (.ics)" }).getAttribute("href");
  expect(href).toContain("/api/feed.ics?type=hackathon");
  const res = await request.get(href!);
  expect(res.headers()["content-type"]).toContain("text/calendar");
  expect(await res.text()).toContain("BEGIN:VCALENDAR");
});

for (const path of ["/", "/calendar/", "/digest/", "/about/", "/start/", "/programs/", "/contribute/", "/data/"]) {
  for (const scheme of ["light", "dark"] as const) {
    test(`no serious accessibility problems on ${path} (${scheme})`, async ({ browser }) => {
      const page = await (await browser.newContext({ colorScheme: scheme })).newPage();
      await page.goto(path);
      await page.waitForLoadState("networkidle"); // check the page with its filters loaded, not the fallback
      const results = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa"]).analyze();
      const serious = results.violations.filter((v) => v.impact === "serious" || v.impact === "critical");
      expect(serious.map((v) => `${v.id}: ${v.nodes[0]?.target}`)).toEqual([]);
    });
  }
}
