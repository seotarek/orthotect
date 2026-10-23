import { chromium } from "playwright-core";
import path from "path";
import fs from "fs";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT_DIR = path.resolve(__dirname, "..");
const SHOWCASE_HTML = path.join(ROOT_DIR, "examples", "golden-showcase", "index.html");

const chromeCandidates = [
  process.env.CHROME_BIN,
  "/usr/bin/google-chrome",
  "/usr/bin/chromium",
  "/usr/bin/chromium-browser"
];
const chromePath = chromeCandidates.find(p => p && fs.existsSync(p));

if (!chromePath) {
  console.error("❌ No Chrome/Chromium executable found.");
  process.exit(1);
}

function parseRgb(colorStr) {
  const match = colorStr.match(/rgba?\((\d+),\s*(\d+),\s*(\d+)/);
  if (!match) return null;
  return [parseInt(match[1], 10), parseInt(match[2], 10), parseInt(match[3], 10)];
}

function channelToLuminance(c) {
  const s = c / 255.0;
  return s <= 0.04045 ? s / 12.92 : Math.pow((s + 0.055) / 1.055, 2.4);
}

function relativeLuminance([r, g, b]) {
  return 0.2126 * channelToLuminance(r) + 0.7152 * channelToLuminance(g) + 0.0722 * channelToLuminance(b);
}

function contrastRatio(rgb1, rgb2) {
  const l1 = relativeLuminance(rgb1);
  const l2 = relativeLuminance(rgb2);
  const lighter = Math.max(l1, l2);
  const darker = Math.min(l1, l2);
  return (lighter + 0.05) / (darker + 0.05);
}

async function evaluateTheme(page, theme) {
  await page.evaluate((t) => {
    document.documentElement.setAttribute("data-theme", t);
  }, theme);
  await page.waitForTimeout(100);

  const targets = [
    { name: "Brand Title on Header Panel", selector: ".brand-title", bgSelector: ".top-bar", threshold: 4.5, type: "normal_text" },
    { name: "Hero Stat Figure on Panel", selector: ".hero-figure", bgSelector: ".hero-stat", threshold: 4.5, type: "large_text" },
    { name: "Hero Label (Secondary Text) on Panel", selector: ".hero-label", bgSelector: ".hero-stat", threshold: 4.5, type: "normal_text" },
    { name: "Primary Action Button Label", selector: "#btn-deploy", bgSelector: "#btn-deploy", useButtonBg: true, threshold: 4.5, type: "action_text" },
    { name: "Destructive Action Button Label", selector: "#btn-rollback", bgSelector: "#btn-rollback", useButtonBg: true, threshold: 4.5, type: "action_text" },
    { name: "Dialog Trigger Button Label", selector: "#btn-open-modal", bgSelector: "#btn-open-modal", useButtonBg: true, threshold: 4.5, type: "action_text" },
  ];


  const results = [];

  for (const t of targets) {
    const data = await page.evaluate(({ selector, bgSelector, useButtonBg }) => {
      const el = document.querySelector(selector);
      if (!el) return null;
      const elStyle = window.getComputedStyle(el);

      let fg = elStyle.color;
      let bg;
      if (useButtonBg) {
        bg = elStyle.backgroundColor;
      } else {
        const bgEl = document.querySelector(bgSelector) || document.body;
        bg = window.getComputedStyle(bgEl).backgroundColor;
      }
      return { fg, bg };
    }, t);

    if (!data) {
      results.push({ name: t.name, status: "SKIPPED", error: "Element not found" });
      continue;
    }

    const fgRgb = parseRgb(data.fg);
    const bgRgb = parseRgb(data.bg);

    if (!fgRgb || !bgRgb) {
      results.push({ name: t.name, status: "ERROR", error: `Unparseable colors: ${data.fg} / ${data.bg}` });
      continue;
    }

    const ratio = contrastRatio(fgRgb, bgRgb);
    const passed = ratio >= t.threshold;
    results.push({
      name: t.name,
      ratio: ratio.toFixed(2),
      threshold: t.threshold,
      passed,
      fg: data.fg,
      bg: data.bg
    });
  }

  return results;
}

async function main() {
  console.log("═══════════════════════════════════════════════════════════════");
  console.log("  ORTHOTECT BROWSER TEST: Rendered DOM Contrast Verification");
  console.log("═══════════════════════════════════════════════════════════════");

  const browser = await chromium.launch({
    executablePath: chromePath,
    headless: true,
    args: ["--no-sandbox", "--disable-setuid-sandbox"]
  });

  const page = await browser.newPage({ viewport: { width: 1280, height: 800 } });
  await page.goto(`file://${SHOWCASE_HTML}`, { waitUntil: "networkidle" });

  let totalTested = 0;
  let totalPassed = 0;
  let hasFailure = false;

  for (const theme of ["light", "dark"]) {
    console.log(`\nBrowser Theme Context: [${theme.toUpperCase()}]`);
    const results = await evaluateTheme(page, theme);
    for (const r of results) {
      totalTested++;
      if (r.passed) {
        totalPassed++;
        console.log(`  ✅ ${r.name.padEnd(42)}: ${r.ratio}:1 [PASS >= ${r.threshold}:1] (fg: ${r.fg}, bg: ${r.bg})`);
      } else {
        hasFailure = true;
        console.log(`  ❌ ${r.name.padEnd(42)}: ${r.ratio}:1 [FAIL < ${r.threshold}:1] (fg: ${r.fg}, bg: ${r.bg})`);
      }
    }
  }

  await browser.close();

  console.log(`\nBrowser Verification Summary: ${totalPassed}/${totalTested} rendered DOM element pairs passed WCAG 2.2.`);
  if (!hasFailure) {
    console.log("✅ [PASS] Real browser computed-style contrast verified across Light and Dark themes.");
    process.exit(0);
  } else {
    console.error("❌ [FAIL] One or more rendered DOM elements failed WCAG contrast criteria.");
    process.exit(1);
  }
}

main().catch(err => {
  console.error("Browser verification fatal error:", err);
  process.exit(1);
});
