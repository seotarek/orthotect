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

function parseRgba(colorStr) {
  if (!colorStr) return null;
  const match = colorStr.match(/rgba?\((\d+),\s*(\d+),\s*(\d+)(?:,\s*([\d.]+))?\)/);
  if (!match) return null;
  const r = parseInt(match[1], 10);
  const g = parseInt(match[2], 10);
  const b = parseInt(match[3], 10);
  const a = match[4] !== undefined ? parseFloat(match[4]) : 1.0;
  return [r, g, b, a];
}

/**
 * Composites a foreground RGBA color over an underlying base RGB color
 * according to W3C alpha blending formula:
 * C_comp = (1 - alpha) * C_bg + alpha * C_fg
 */
function compositeColor([fgR, fgG, fgB, alpha], [bgR, bgG, bgB]) {
  if (alpha >= 1.0) return [fgR, fgG, fgB];
  return [
    Math.round((1 - alpha) * bgR + alpha * fgR),
    Math.round((1 - alpha) * bgG + alpha * fgG),
    Math.round((1 - alpha) * bgB + alpha * fgB)
  ];
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
    { name: "Card Title (Secondary Text) on Panel", selector: ".card-title", bgSelector: ".card", threshold: 4.5, type: "normal_text" },
    { name: "Card Value (Primary Text) on Panel", selector: ".card-val", bgSelector: ".card", threshold: 4.5, type: "normal_text" },
    { name: "Table Header Text on Subtle Surface", selector: "th", bgSelector: "th", threshold: 4.5, type: "normal_text" },
    { name: "Table Cell Text on Panel", selector: "td", bgSelector: ".table-container", threshold: 4.5, type: "normal_text" },
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
      const fg = elStyle.color;

      // Recursive ancestor traversal to collect all backdrop layers from element up to documentElement
      const bgLayers = [];
      if (useButtonBg) {
        bgLayers.push(elStyle.backgroundColor);
      }
      let curr = useButtonBg ? el.parentElement : (document.querySelector(bgSelector) || el);
      while (curr && curr.nodeType === 1) {
        const bg = window.getComputedStyle(curr).backgroundColor;
        if (bg && bg !== "transparent" && bg !== "rgba(0, 0, 0, 0)") {
          bgLayers.push(bg);
        }
        curr = curr.parentElement;
      }
      const canvasBg = window.getComputedStyle(document.body).backgroundColor;
      const directBg = useButtonBg ? elStyle.backgroundColor : window.getComputedStyle(document.querySelector(bgSelector) || el).backgroundColor;
      return { fg, bgLayers, canvasBg, directBg };
    }, t);

    if (!data) {
      results.push({ name: t.name, status: "SKIPPED", error: "Element not found" });
      continue;
    }

    const fgRgba = parseRgba(data.fg);
    const canvasRgba = parseRgba(data.canvasBg) || [255, 255, 255, 1.0];

    if (!fgRgba) {
      results.push({ name: t.name, status: "ERROR", error: `Unparseable foreground: ${data.fg}` });
      continue;
    }

    // Mathematical W3C multi-layer compositing: start from canvas base and composite down the tree
    let effectiveBgRgb = [canvasRgba[0], canvasRgba[1], canvasRgba[2]];
    const orderedLayers = data.bgLayers.slice().reverse();
    for (const layerStr of orderedLayers) {
      const layerRgba = parseRgba(layerStr);
      if (layerRgba) {
        effectiveBgRgb = compositeColor(layerRgba, effectiveBgRgb);
      }
    }

    // Alpha compositing for foreground against effective composite background if translucent
    const effectiveFgRgb = fgRgba[3] < 1.0 ? compositeColor(fgRgba, effectiveBgRgb) : [fgRgba[0], fgRgba[1], fgRgba[2]];

    const ratio = contrastRatio(effectiveFgRgb, effectiveBgRgb);
    const passed = ratio >= t.threshold;
    results.push({
      name: t.name,
      ratio: ratio.toFixed(2),
      threshold: t.threshold,
      passed,
      fg: data.fg,
      bg: data.directBg
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
