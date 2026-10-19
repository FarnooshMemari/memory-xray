import { devices, expect, test, type Page } from "@playwright/test";

// Regenerates the screenshots in screenshots/. Run with: npm run screenshots
test.skip(!process.env.SCREENSHOTS, "set SCREENSHOTS=1 to regenerate screenshots");
test.skip(({ isMobile }) => isMobile, "desktop project drives both sizes");

const OUT = "screenshots";
const settle = (page: Page, ms = 1800) => page.waitForTimeout(ms);
const hideCursor = (page: Page) => page.addStyleTag({ content: "*{caret-color:transparent !important}" });

test("desktop screenshots", async ({ browser }) => {
  test.setTimeout(180_000);
  const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 }, deviceScaleFactor: 2 });
  const page = await ctx.newPage();

  await page.goto("/#s_single/o0/m15");
  await hideCursor(page);
  await settle(page, 2400);
  await page.screenshot({ path: `${OUT}/01-desktop-first-view.png` });

  // the sticky masthead would otherwise be drawn over element captures taller than the viewport
  const mast = await page.addStyleTag({ content: ".masthead{visibility:hidden !important}" });
  const film = async (hash: string, name: string, before?: () => Promise<void>) => {
    await page.evaluate((h) => { window.location.hash = h; }, hash);
    if (before) await before();
    await settle(page);
    await page.locator("#instrument").evaluate((el) => window.scrollTo(0, el.getBoundingClientRect().top + window.scrollY - 62));
    await settle(page, 400);
    await page.locator(".film").screenshot({ path: `${OUT}/${name}` });
  };
  await film("s_redundant/o0/m14", "02-instrument-redundancy-one-report-removed.png");
  await film("s_conflict/o2/m15", "03-instrument-conflict-rate-cut-last.png");
  await film("s_conflict/o0/m15", "04-instrument-citations-injected-decision.png", async () => {
    const b = page.getByRole("button", { name: "What the model cited" });
    if ((await b.getAttribute("aria-pressed")) !== "true") await b.click();
  });
  await page.getByRole("button", { name: "What the model cited" }).click();

  await page.evaluate(() => { window.location.hash = "s_redundant/o0/m15"; });
  await page.locator('#combinations .chip', { hasText: "Press release" }).click();
  await settle(page);
  await page.locator("#combinations").screenshot({ path: `${OUT}/05-lattice-shapley-vs-leave-one-out.png` });

  await page.evaluate(() => { window.location.hash = "s_conflict/o0/m15"; });
  await settle(page);
  await page.locator("#citations").screenshot({ path: `${OUT}/06-what-it-says-vs-what-moves-it.png` });
  await page.locator("#catch").screenshot({ path: `${OUT}/07-the-catch-content-only-citer.png` });
  await mast.evaluate((el) => (el as HTMLElement).remove());

  await page.evaluate(() => window.scrollTo(0, 0));
  await page.getByRole("button", { name: "Take the 40-second tour" }).click();
  await page.getByRole("dialog").getByRole("button", { name: "Next" }).click();
  await page.getByRole("dialog").getByRole("button", { name: "Next" }).click();
  await settle(page, 2000);
  await page.screenshot({ path: `${OUT}/08-guided-tour.png` });
  await page.keyboard.press("Escape");

  await page.goto("/#macro_a/o0/m15");
  await page.evaluate(() => window.scrollTo(0, 0));
  await settle(page, 2400);
  await page.screenshot({ path: `${OUT}/09-desktop-full-page.png`, fullPage: true });
  await ctx.close();
});

test("mobile screenshots", async ({ browser }) => {
  test.setTimeout(120_000);
  const ctx = await browser.newContext({ ...devices["Pixel 7"] });
  const page = await ctx.newPage();
  await page.goto("/#s_redundant/o0/m15");
  await hideCursor(page);
  await settle(page, 2200);
  await page.screenshot({ path: `${OUT}/10-mobile-first-view.png` });
  await page.locator("#instrument").evaluate((el) => window.scrollTo(0, el.getBoundingClientRect().top + window.scrollY - 60));
  await settle(page, 500);
  await page.screenshot({ path: `${OUT}/11-mobile-instrument.png` });
  await page.locator('.slip[data-record="E1"]').click();
  await page.locator('.slip[data-record="E3"]').click();
  await settle(page, 1200);
  await expect(page.getByTestId("gauge")).toBeInViewport();
  await page.screenshot({ path: `${OUT}/12-mobile-two-reports-removed.png` });
  await page.locator("#catch").scrollIntoViewIfNeeded();
  await settle(page, 800);
  await page.screenshot({ path: `${OUT}/13-mobile-the-catch.png` });
  await page.locator("#combinations .lattice-svg").scrollIntoViewIfNeeded();
  await page.locator("#combinations .lattice-svg").evaluate((el) => window.scrollTo(0, el.getBoundingClientRect().top + window.scrollY - 150));
  await settle(page, 800);
  await page.screenshot({ path: `${OUT}/14-mobile-every-combination.png` });
  await ctx.close();
});
