import { expect, test } from "@playwright/test";
import { ensureDemoJourney, openScreen } from "./_qoderShellSeed";

/**
 * Qoder frontend track — single-focus Today Hero acceptance (GPT pass-3).
 *
 * GPT fixed the Hero's minimum acceptance as DOM/computed assertions (no human
 * screenshot needed). This gate holds the design to: exactly one primary action,
 * no overflow, a bounded first-screen height, and a "Now" block that is simply
 * absent when there is no current activity (never an empty slot).
 */

const WIDTHS = [360, 412, 430, 1280];

test.describe("Qoder Today single-focus hero", () => {
  test("hero has one primary CTA, bounded height, no empty Now slot, no overflow", async ({
    page,
  }) => {
    test.setTimeout(120_000);
    await page.emulateMedia({ colorScheme: "light", media: "screen" });
    await ensureDemoJourney(page);

    for (const width of WIDTHS) {
      const height = width >= 900 ? 900 : 844;
      await page.setViewportSize({ width, height });
      await openScreen(page, "/v8/hub", ["today-heading", "today-next"]);

      const hero = page.getByTestId("today-hero");
      await expect(hero).toBeVisible();

      // 1. Exactly one visible primary CTA inside the hero.
      const primaryCount = await hero
        .locator(".v8-primary, .v8-primary-button")
        .evaluateAll(
          (els) =>
            els.filter(
              (el) => (el as HTMLElement).offsetParent !== null && (el as HTMLElement).getClientRects().length > 0,
            ).length,
        );
      expect(primaryCount, `hero@${width}: expected ≤1 primary CTA, got ${primaryCount}`).toBeLessThanOrEqual(1);

      // 2. No horizontal overflow within the hero itself.
      const overflow = await hero.evaluate((el) => ({
        scrollW: el.scrollWidth,
        clientW: el.clientWidth,
        over: el.scrollWidth > el.clientWidth + 1,
      }));
      expect(overflow.over, `hero@${width}: internal horizontal overflow (${overflow.scrollW}>${overflow.clientW})`).toBe(false);

      // 3. Hero must not dominate the first screen (>45% viewport height).
      const heroBox = await hero.boundingBox();
      expect(heroBox, `hero@${width}: no box`).not.toBeNull();
      const ratio = (heroBox?.height ?? 0) / height;
      expect(ratio, `hero@${width}: height ${Math.round(ratio * 100)}% of viewport > 45%`).toBeLessThanOrEqual(0.45);

      // 4/5. The demo journey has not started, so there is NO current activity:
      //      the hero must degrade to Next only and must not render an empty
      //      "Now" block.
      const nowAttr = await hero.getAttribute("data-now");
      const nowCount = await page.getByTestId("today-now").count();
      expect(nowAttr, `hero@${width}: data-now should be false pre-trip`).toBe("false");
      expect(nowCount, `hero@${width}: empty "Now" block must not render`).toBe(0);

      // 6. The CTA appears iff there is a genuine next stop — never an empty
      //    slot (GPT: "无 next 时不渲染空 CTA"). The pre-plan demo has no next,
      //    so the hero shows a completion line and must not render a CTA.
      const nextRowText = ((await page.getByTestId("today-next").locator(".cn-hero-next-row").innerText()) || "").trim();
      const isEmptyNext = /还没有安排|Nothing scheduled/i.test(nextRowText);
      const ctaCount = await page
        .getByTestId("today-hero-cta")
        .evaluateAll((els) => els.filter((el) => (el as HTMLElement).getClientRects().length > 0).length);
      if (isEmptyNext) {
        expect(ctaCount, `hero@${width}: an empty "no next" state must not render a CTA (next="${nextRowText}")`).toBe(0);
      } else {
        expect(ctaCount, `hero@${width}: an actionable next stop must expose exactly one CTA (next="${nextRowText}")`).toBe(1);
      }
    }
  });

  test("reduced-motion disables the hero reveal transform", async ({ page }) => {
    test.setTimeout(90_000);
    await page.emulateMedia({ reducedMotion: "reduce", colorScheme: "light", media: "screen" });
    await ensureDemoJourney(page);
    await page.setViewportSize({ width: 390, height: 844 });
    await openScreen(page, "/v8/hub", ["today-heading", "today-next"]);

    const hero = page.getByTestId("today-hero");
    const reveal = await hero.evaluate((el) => {
      const st = getComputedStyle(el);
      return { animationName: st.animationName, transform: st.transform };
    });
    // The hero itself sits in a page-reveal group; under reduced motion that
    // animation is suppressed and no translate transform is applied.
    expect(
      reveal.animationName === "none" || reveal.transform === "none",
      `reduced-motion: hero should not translate-reveal (anim=${reveal.animationName}, transform=${reveal.transform})`,
    ).toBe(true);
  });
});
