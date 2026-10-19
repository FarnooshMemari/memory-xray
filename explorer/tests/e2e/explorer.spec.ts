import { expect, test, type Page } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import fs from "node:fs";
import path from "node:path";

// The tests compare what the page shows with the saved data file it was built from.
const DATA = JSON.parse(fs.readFileSync(path.resolve("src/data/explorer-data.json"), "utf8"));
const LABELS = ["Positive", "Neutral", "Negative"] as const;
const RECS = ["E1", "E2", "E3", "E4"] as const;
const bit = (r: string) => 1 << RECS.indexOf(r as (typeof RECS)[number]);
const scen = (id: string) => DATA.scenarios.find((s: { id: string }) => s.id === id);
const vOf = (s: any, o: any, m: number) => o.subsets[String(m)].p[LABELS.indexOf(s.dStar)];

async function go(page: Page, hash: string) {
  await page.evaluate((h) => { window.location.hash = h; }, hash);
  await expect(page.getByTestId("gauge")).toHaveAttribute("data-mask", hash.split("/m")[1]);
}

test.describe("desktop", () => {
  test.skip(({ isMobile }) => isMobile, "desktop only");

  test("loads with no console errors and shows the default scenario", async ({ page }) => {
    const errors: string[] = [];
    page.on("pageerror", (e) => errors.push(String(e)));
    page.on("console", (m) => { if (m.type() === "error") errors.push(m.text()); });
    await page.goto("/");
    await expect(page.getByRole("heading", { level: 1 })).toContainText("cite the evidence");
    await expect(page.getByTestId("gauge")).toHaveAttribute("data-answer", "Positive");
    expect(errors).toEqual([]);
  });

  test("every one of the 288 saved combinations is shown exactly as saved", async ({ browser }) => {
    test.setTimeout(300_000);
    // reduced motion: values are shown at once, so each of the 288 states can be read immediately
    const ctx = await browser.newContext({ reducedMotion: "reduce", viewport: { width: 1440, height: 900 } });
    const page = await ctx.newPage();
    await page.goto("/");
    for (const s of DATA.scenarios) {
      for (const o of s.orderings) {
        for (let m = 0; m < 16; m++) {
          await go(page, `${s.id}/o${o.index}/m${m}`);
          const g = page.getByTestId("gauge");
          const c = o.subsets[String(m)];
          await expect(g).toHaveAttribute("data-answer", c.argmax);
          expect((await g.getAttribute("data-p"))!.split(",").map(Number)).toEqual(c.p);
          for (let i = 0; i < 3; i++) {
            await expect(g.locator(`.bar-row[data-label="${LABELS[i]}"] .bar-val`)).toHaveText(c.p[i].toFixed(2));
          }
          // each record's pull equals the saved lattice difference v(S with it) - v(S without it)
          for (const r of RECS) {
            const want = vOf(s, o, m | bit(r)) - vOf(s, o, m & ~bit(r));
            const got = Number(await page.locator(`.stage-svg path[data-record="${r}"]`).getAttribute("data-effect"));
            expect(Math.abs(got - want)).toBeLessThan(1e-12);
          }
        }
      }
    }
    await ctx.close();
  });

  test("pressing a record removes and restores it, and updates the answer", async ({ page }) => {
    await page.goto("/#s_redundant/o0/m15");
    const s = scen("s_redundant"), o = s.orderings[0];
    await page.locator('.slip[data-record="E1"]').click();
    await expect(page.getByTestId("gauge")).toHaveAttribute("data-mask", "14");
    await page.locator('.slip[data-record="E3"]').click();
    await expect(page.getByTestId("gauge")).toHaveAttribute("data-mask", "10");
    await expect(page.getByTestId("gauge")).toHaveAttribute("data-answer", o.subsets["10"].argmax);
    await expect(page.locator('.slip[data-record="E1"]')).toHaveAttribute("aria-pressed", "false");
    await expect(page).toHaveURL(/#s_redundant\/o0\/m10$/);
    await page.getByRole("button", { name: "Show all four" }).click();
    await expect(page.getByTestId("gauge")).toHaveAttribute("data-mask", "15");
  });

  test("orderings reorder the records as the model saw them", async ({ page }) => {
    await page.goto("/#s_conflict/o0/m15");
    const s = scen("s_conflict");
    for (const o of s.orderings) {
      await page.locator(".ord").nth(o.index).click();
      await expect(page.locator(".slips .slip")).toHaveCount(4);
      await expect.poll(async () => page.locator(".slips .slip").evaluateAll((els) => els.map((e) => (e as HTMLElement).dataset.record)))
        .toEqual(o.order);
      await expect(page.getByTestId("gauge")).toHaveAttribute("data-answer", o.fullArgmax);
    }
  });

  test("citation layer marks the injected decision where the model's own answer differed", async ({ page }) => {
    await page.goto("/#s_conflict/o0/m15");
    await page.getByRole("button", { name: "What the model cited" }).click();
    await expect(page.locator(".cite-ticks").first()).toBeVisible();
    await expect(page.locator(".film-note")).toContainText("injected decision");
    const replies = scen("s_conflict").citations.filter((c: any) => c.ordering === 0);
    await expect(page.locator('.slip[data-record="E1"] .cite-tick')).toHaveCount(replies.length);
    await expect(page.locator(".inject-banner")).toContainText(`told the answer was ${scen("s_conflict").dStar}`);
    await page.locator(".ord").nth(2).click();
    await expect(page.locator(".film-note")).not.toContainText("injected decision");
    await expect(page.locator(".inject-banner")).toHaveCount(0);
    // the ledger flags exactly the misaligned orderings of this scenario
    await expect(page.locator("#citations .ledger .inject-note")).toHaveCount(scen("s_conflict").misalignedOrderings.length);
  });

  test("lattice nodes load a combination into the instrument", async ({ page }) => {
    await page.goto("/#macro_a/o1/m15");
    await page.locator('#combinations .lattice-node[aria-label^="E1, E3:"]').click();
    await expect(page.getByTestId("gauge")).toHaveAttribute("data-mask", String(bit("E1") | bit("E3")));
    const shap = scen("macro_a").orderings[1].shapley.E3;
    await page.locator('#combinations .chip', { hasText: "Manufacturing PMI" }).click();
    await expect(page.locator("#combinations .callout")).toContainText((shap < 0 ? "−" : "+") + Math.abs(shap).toFixed(2));
  });

  test("the tour steps through real saved states and closes", async ({ page }) => {
    await page.goto("/");
    await page.getByRole("button", { name: "Take the 40-second tour" }).click();
    const dialog = page.getByRole("dialog");
    await expect(dialog).toContainText("Step 1 of 8");
    await expect(page).toHaveURL(/#s_redundant\/o0\/m15$/);
    await dialog.getByRole("button", { name: "Next" }).click();
    await expect(page).toHaveURL(/#s_redundant\/o0\/m14$/);
    const s = scen("s_redundant");
    await expect(dialog).toContainText(vOf(s, s.orderings[0], 14).toFixed(2));
    for (let i = 0; i < 4; i++) await dialog.getByRole("button", { name: "Next" }).click();
    await expect(page).toHaveURL(/#s_conflict\/o2\/m15$/);
    await expect(dialog).toContainText("12 of 12");
    await page.keyboard.press("Escape");
    await expect(dialog).toHaveCount(0);
  });

  test("keyboard: scenario radios and record buttons work without a mouse", async ({ page }) => {
    await page.goto("/#s_single/o0/m15");
    await page.locator('.tab[data-scenario="s_single"]').focus();
    await page.keyboard.press("ArrowRight");
    await expect(page).toHaveURL(/#s_redundant\//);
    await expect(page.locator('.tab[data-scenario="s_redundant"]')).toBeFocused();
    await page.locator('.slip[data-record="E2"]').focus();
    await page.keyboard.press("Space");
    await expect(page.locator('.slip[data-record="E2"]')).toHaveAttribute("aria-pressed", "false");
  });

  test("arrow keys move within each radio group, and the tour does not take them over", async ({ page }) => {
    await page.goto("/#s_conflict/o0/m15");
    await page.locator('.ord[aria-checked="true"]').focus();
    await page.keyboard.press("ArrowRight");
    await expect(page).toHaveURL(/#s_conflict\/o1\//);
    await expect(page.locator(".ord").nth(1)).toBeFocused();
    await page.locator('#combinations .chip[aria-checked="true"]').focus();
    await page.keyboard.press("End");
    await expect(page.locator("#combinations .chip").nth(3)).toHaveAttribute("aria-checked", "true");
    // with the tour open, arrow keys on the scenario tabs still change the scenario, not the tour step
    const tourButton = page.getByRole("button", { name: "Take the 40-second tour" });
    await tourButton.click();
    const dialog = page.getByRole("dialog");
    await expect(dialog).toContainText("Step 1 of 8");
    await expect(page).toHaveURL(/#s_redundant\/o0\/m15$/); // the tour's first step has loaded its view
    await page.locator('.tab[aria-checked="true"]').focus();
    await page.keyboard.press("ArrowRight");
    await expect(dialog).toContainText("Step 1 of 8");
    await expect(page).toHaveURL(/#s_conflict\//);
    await dialog.getByRole("button", { name: "Next" }).focus();
    await page.keyboard.press("ArrowRight");
    await expect(dialog).toContainText("Step 2 of 8");
    await page.keyboard.press("Escape");
    await expect(tourButton).toBeFocused();
  });

  test("has no serious accessibility violations", async ({ page }) => {
    await page.goto("/#s_conflict/o0/m15");
    await page.waitForTimeout(800);
    const results = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa"]).analyze();
    const serious = results.violations.filter((v) => v.impact === "serious" || v.impact === "critical");
    expect(serious.map((v) => `${v.id}: ${v.nodes.length}`)).toEqual([]);
  });

  test("respects reduced motion", async ({ browser }) => {
    const ctx = await browser.newContext({ reducedMotion: "reduce", viewport: { width: 1440, height: 900 } });
    const page = await ctx.newPage();
    await page.goto("/#s_single/o0/m15");
    await page.locator('.slip[data-record="E2"]').click();
    await expect(page.getByTestId("gauge")).toHaveAttribute("data-answer", scen("s_single").orderings[0].subsets["13"].argmax);
    await expect(page.getByTestId("gauge").locator(".bar-row.is-top .bar-val")).toHaveText(
      Math.max(...scen("s_single").orderings[0].subsets["13"].p).toFixed(2));
    await ctx.close();
  });
});

test.describe("mobile", () => {
  test.skip(({ isMobile }) => !isMobile, "mobile only");

  test("the answer stays in view while records are toggled", async ({ page }) => {
    await page.goto("/#s_redundant/o0/m15");
    await page.locator('.slip[data-record="E4"]').scrollIntoViewIfNeeded();
    await page.locator('.slip[data-record="E4"]').click();
    await expect(page.getByTestId("gauge")).toBeInViewport();
    await expect(page.getByTestId("gauge")).toHaveAttribute("data-mask", "7");
  });

  test("has no horizontal overflow", async ({ page }) => {
    await page.goto("/#macro_b/o1/m15");
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
    expect(overflow).toBeLessThanOrEqual(0);
  });
});
