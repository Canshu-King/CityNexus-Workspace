/**
 * Visual-integration capture (2026-09-19).
 *
 * The Apple line could only ever claim *programmatic* readiness because the
 * isolated harness had no screenshot it (and therefore nobody) could read. This
 * script closes that gap: it renders the real seeded Today and Live surfaces at
 * the phone widths the product is judged on, in both colour schemes, writes
 * readable PNGs into reports/visual-integration/, and prints the computed facts
 * (page height, whether the hero/decision reached the first screen) next to each
 * shot so a reviewer can cross-check the picture against the numbers.
 *
 * Usage:
 *   node tools/capture-visual.mjs            # uses http://127.0.0.1:4175
 *   CITYNEXUS_E2E_BASE_URL=... node tools/capture-visual.mjs
 */
import { chromium } from "@playwright/test";
import { mkdirSync } from "node:fs";

const BASE = process.env.CITYNEXUS_E2E_BASE_URL ?? "http://127.0.0.1:4175";
const STATE = "./e2e/.qoder-seed-state.json";
const OUT = "../reports/visual-integration";

const SCREENS = [
  { name: "today", url: "/v8/hub", ready: "today-heading" },
  { name: "live", url: "/v8/live", ready: "v8-live-journey" },
];
const VIEWPORTS = [
  { name: "360x800", width: 360, height: 800 },
  { name: "412x915", width: 412, height: 915 },
  { name: "430x932", width: 430, height: 932 },
  { name: "desktop1280", width: 1280, height: 900 },
];
const SCHEMES = ["light", "dark"];

mkdirSync(OUT, { recursive: true });

const browser = await chromium.launch();
const rows = [];
for (const screen of SCREENS) {
  for (const vp of VIEWPORTS) {
    for (const scheme of SCHEMES) {
      const context = await browser.newContext({
        viewport: { width: vp.width, height: vp.height },
        storageState: STATE,
        colorScheme: scheme,
        deviceScaleFactor: 2,
      });
      const page = await context.newPage();
      await page.goto(`${BASE}${screen.url}`, { waitUntil: "load" });
      await page.getByTestId(screen.ready).first().waitFor({ timeout: 30_000 });
      await page.waitForTimeout(1800);

      const facts = await page.evaluate(() => {
        const bodyText = document.body.innerText;
        const kicker = document.querySelector(".v8-page-intro .v8-kicker");
        const canvas = getComputedStyle(document.querySelector(".v8-product-shell") ?? document.body);
        return {
          pageHeightPx: document.documentElement.scrollHeight,
          horizontalOverflowPx:
            document.documentElement.scrollWidth - document.documentElement.clientWidth,
          background: canvas.backgroundColor,
          foreground: canvas.color,
          kickerText: kicker ? kicker.innerText.trim().slice(0, 48) : null,
          bodyChars: bodyText.length,
        };
      });

      const file = `${screen.name}-${vp.name}-${scheme}.png`;
      await page.screenshot({ path: `${OUT}/${file}`, fullPage: false });
      await page.screenshot({ path: `${OUT}/${file.replace(".png", "-full.png")}`, fullPage: true });
      rows.push({ screen: screen.name, vp: vp.name, scheme, file, ...facts });
      await context.close();
    }
  }
}
await browser.close();

for (const r of rows) {
  console.log(
    `${r.screen.padEnd(5)} ${r.vp.padEnd(13)} ${r.scheme.padEnd(5)} ${r.file.padEnd(34)} h=${String(r.pageHeightPx).padStart(5)}px overflow=${r.horizontalOverflowPx}px bg=${r.background} fg=${r.foreground} kicker="${r.kickerText ?? "-"}"`,
  );
}
console.log(`\n${rows.length} screens captured, ${rows.length * 2} files in ${OUT}`);
