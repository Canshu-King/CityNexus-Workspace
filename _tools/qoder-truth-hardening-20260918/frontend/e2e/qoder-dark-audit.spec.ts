import { expect, test } from "@playwright/test";
import { mkdirSync, writeFileSync } from "node:fs";
import { ensureDemoJourney, openScreen } from "./_qoderShellSeed";
import { scanContrast, type Violation } from "./_qoderContrastScan";

/**
 * Qoder frontend track — dark-mode gate on the real Today (/v8/hub) and Live
 * (/v8/live) surfaces (GPT calls #1 + #5). The four-tier contrast judgement
 * lives in _qoderContrastScan.ts and is shared with the mocked Live state gate,
 * so "0 violations" means the same thing everywhere. Legacy / Advanced /
 * Wallet-JSON / off-path panels stay declared debt.
 */

const OUT_DIR = "../reports/dark-audit";

interface AuditReport {
  screen: string;
  scanned: number;
  violations: Violation[];
  borderWarnings: number;
}

async function auditScreen(
  page: import("@playwright/test").Page,
  url: string,
  readyTestIds: string[],
  screen: string,
): Promise<AuditReport> {
  await page.emulateMedia({ colorScheme: "dark", media: "screen" });
  await page.goto(url, { waitUntil: "load" });
  for (const id of readyTestIds) {
    await expect(page.getByTestId(id).first()).toBeVisible({ timeout: 25_000 });
  }
  await page.waitForTimeout(1500);
  const scanned = await scanContrast(page);
  return {
    screen,
    scanned: scanned.count,
    violations: scanned.rows,
    borderWarnings: scanned.warnings,
  };
}

interface FocusVerdict {
  selector: string;
  testId: string | null;
  outlineStyle: string;
  outlineWidth: number;
  outlineColor: string;
  hasRing: boolean;
  contrast: number;
}

async function auditFocusRing(
  page: import("@playwright/test").Page,
): Promise<Violation[]> {
  const violations: Violation[] = [];
  await page.evaluate(() => (document.activeElement as HTMLElement | null)?.blur?.());
  const seen = new Set<string>();
  for (let i = 0; i < 22; i += 1) {
    await page.keyboard.press("Tab");
    const verdict = await page.evaluate(() => {
      const parse = (value: string): [number, number, number, number] => {
        const m = value.match(/rgba?\(([^)]+)\)/);
        if (!m) return [0, 0, 0, value === "transparent" ? 0 : 1];
        const p = m[1].split(",").map((x) => parseFloat(x.trim()));
        return [p[0] || 0, p[1] || 0, p[2] || 0, p.length > 3 ? p[3] : 1];
      };
      const channel = (c: number) => {
        const s = c / 255;
        return s <= 0.03928 ? s / 12.92 : Math.pow((s + 0.055) / 1.055, 2.4);
      };
      const lum = (rgb: [number, number, number]) =>
        0.2126 * channel(rgb[0]) + 0.7152 * channel(rgb[1]) + 0.0722 * channel(rgb[2]);
      const contrast = (a: [number, number, number], b: [number, number, number]) => {
        const la = lum(a);
        const lb = lum(b);
        return (Math.max(la, lb) + 0.05) / (Math.min(la, lb) + 0.05);
      };
      const backgroundUnder = (el: Element): [number, number, number] => {
        const stack: Array<[number, number, number, number]> = [];
        let cur: Element | null = el;
        while (cur) {
          const bg = parse(getComputedStyle(cur).backgroundColor);
          if (bg[3] > 0) {
            stack.push(bg);
            if (bg[3] >= 0.999) break;
          }
          cur = cur.parentElement;
        }
        let acc: [number, number, number] = [0, 0, 0];
        for (let i = stack.length - 1; i >= 0; i--) {
          const f = stack[i];
          acc = [f[0] * f[3] + acc[0] * (1 - f[3]), f[1] * f[3] + acc[1] * (1 - f[3]), f[2] * f[3] + acc[2] * (1 - f[3])];
        }
        return acc;
      };
      const el = document.activeElement as HTMLElement | null;
      if (!el || el === document.body || !el.matches("button,a,input,textarea,[tabindex],[role=button]"))
        return null;
      const rect = el.getBoundingClientRect();
      if (rect.width < 2 || rect.height < 2) return null;
      const st = getComputedStyle(el);
      const outlineWidth = parseFloat(st.outlineWidth) || 0;
      const outlineColor = st.outlineColor === "currentcolor" ? st.color : st.outlineColor;
      const box = st.boxShadow;
      const hasRing = box && box !== "none";
      const surround = backgroundUnder(el.parentElement ?? el);
      const oc = parse(outlineColor);
      const ringContrast =
        st.outlineStyle !== "none" && outlineWidth > 0 && oc[3] > 0.2
          ? contrast(
              [oc[0] * oc[3] + surround[0] * (1 - oc[3]), oc[1] * oc[3] + surround[1] * (1 - oc[3]), oc[2] * oc[3] + surround[2] * (1 - oc[3])],
              surround,
            )
          : 0;
      const tid = el.getAttribute("data-testid");
      const cls = (el.getAttribute("class") || "").split(/\s+/).filter(Boolean).slice(0, 2).join(".");
      return {
        selector: tid ? `[data-testid="${tid}"]` : `${el.tagName.toLowerCase()}${cls ? "." + cls : ""}`,
        testId: tid,
        outlineStyle: st.outlineStyle,
        outlineWidth,
        outlineColor,
        hasRing: !!hasRing,
        contrast: Math.round(ringContrast * 100) / 100,
      } as FocusVerdict;
    });

    if (!verdict) continue;
    if (seen.has(verdict.selector)) break;
    seen.add(verdict.selector);

    const indicator = verdict.outlineStyle !== "none" && verdict.outlineWidth >= 2;
    if (!indicator && !verdict.hasRing) {
      violations.push({
        kind: "control-boundary",
        selector: verdict.selector,
        testId: verdict.testId,
        text: "no focus indicator",
        color: verdict.outlineColor,
        background: "",
        fontSizePx: 0,
        bold: false,
        contrast: 0,
        required: 3,
      });
    } else if (indicator && verdict.contrast < 3) {
      violations.push({
        kind: "control-boundary",
        selector: verdict.selector,
        testId: verdict.testId,
        text: `focus ring ${verdict.outlineWidth}px vs surround`,
        color: verdict.outlineColor,
        background: "",
        fontSizePx: 0,
        bold: false,
        contrast: verdict.contrast,
        required: 3,
      });
    }
  }
  return violations;
}

function summarise(reports: AuditReport[]): string {
  const lines: string[] = [];
  for (const r of reports) {
    lines.push(`\n=== ${r.screen} (dark) — scanned ${r.scanned} nodes, ${r.violations.length} violation(s), ${r.borderWarnings} decorative-border warning(s) ===`);
    const byKind = new Map<string, Violation[]>();
    for (const v of r.violations) {
      if (!byKind.has(v.kind)) byKind.set(v.kind, []);
      byKind.get(v.kind)!.push(v);
    }
    for (const [kind, items] of byKind) {
      lines.push(`  -- ${kind}: ${items.length}`);
      for (const v of items.slice(0, 25))
        lines.push(`     ${v.selector} "${v.text}" fg=${v.color} bg=${v.background} c=${v.contrast}/${v.required} ${v.fontSizePx}px`);
    }
  }
  return lines.join("\n");
}

test.describe("Qoder dark-mode audit (Today + Live)", () => {
  for (const vp of [
    { width: 390, height: 844, name: "mobile" },
    { width: 1280, height: 900, name: "desktop" },
  ]) {
    test(`no dark contrast violations on Today/Live (${vp.name})`, async ({ page }) => {
      test.setTimeout(120_000);
      await page.setViewportSize({ width: vp.width, height: vp.height });
      await ensureDemoJourney(page);
      const today = await auditScreen(page, "/v8/hub", ["today-heading"], `today/${vp.name}`);
      const live = await auditScreen(page, "/v8/live", ["v8-live-journey"], `live/${vp.name}`);
      const reports = [today, live];
      mkdirSync(OUT_DIR, { recursive: true });
      writeFileSync(`${OUT_DIR}/dark-audit-${vp.name}.json`, JSON.stringify(reports, null, 2), "utf8");
      console.log(summarise(reports));
      const all = reports.flatMap((r) => r.violations.map((v) => `${r.screen}: ${v.kind} ${v.selector} "${v.text}"`));
      expect(all, `dark contrast violations (${vp.name}):\n${all.slice(0, 40).join("\n")}`).toEqual([]);
    });

    test(`focus indicators clear 3:1 on Today/Live (${vp.name})`, async ({ page }) => {
      test.setTimeout(120_000);
      await page.setViewportSize({ width: vp.width, height: vp.height });
      await page.emulateMedia({ colorScheme: "dark", media: "screen" });
      await ensureDemoJourney(page);
      await openScreen(page, "/v8/hub", ["today-heading"]);
      const todayFocus = await auditFocusRing(page);
      await openScreen(page, "/v8/live", ["v8-live-journey"]);
      const liveFocus = await auditFocusRing(page);
      const lines = [...todayFocus, ...liveFocus].map((v) => `${v.selector} "${v.text}" ${v.contrast}/${v.required}`);
      expect(lines, `dark focus violations (${vp.name}):\n${lines.join("\n")}`).toEqual([]);
    });
  }
});
