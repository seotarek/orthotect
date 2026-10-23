import { chromium } from "playwright-core";
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT_DIR = path.resolve(__dirname, "..");
const DOCS_DIR = path.join(ROOT_DIR, "docs");
const TEMPLATES_DIR = path.join(DOCS_DIR, "templates");
const THUMBNAILS_DIR = path.join(DOCS_DIR, "assets", "thumbnails");

if (!fs.existsSync(THUMBNAILS_DIR)) {
  fs.mkdirSync(THUMBNAILS_DIR, { recursive: true });
}

// Find chrome executable
const chromeCandidates = [
  process.env.CHROME_BIN,
  "/usr/bin/google-chrome",
  "/usr/bin/chromium",
  "/usr/bin/chromium-browser"
];
const chromePath = chromeCandidates.find(p => p && fs.existsSync(p));

if (!chromePath) {
  console.error("No chrome executable found!");
  process.exit(1);
}

async function captureAll() {
  const files = fs.readdirSync(TEMPLATES_DIR).filter(f => f.endsWith(".html"));
  console.log(`Found ${files.length} templates to capture...`);

  const browser = await chromium.launch({
    executablePath: chromePath,
    args: ["--no-sandbox", "--disable-setuid-sandbox", "--disable-gpu"]
  });

  const context = await browser.newContext({
    viewport: { width: 1200, height: 750 },
    deviceScaleFactor: 1
  });

  const page = await context.newPage();

  let count = 0;
  for (const file of files) {
    const id = file.replace(".html", "");
    const templatePath = path.join(TEMPLATES_DIR, file);
    const outputPath = path.join(THUMBNAILS_DIR, `${id}.webp`);

    try {
      await page.goto(`file://${templatePath}`, { waitUntil: "load" });
      await page.waitForTimeout(60);

      // Try capturing the content section or main wrapper for maximum visual fidelity
      const targetEl = await page.$(".template-content-section") || await page.$("main");

      if (targetEl) {
        // Capture element screenshot directly
        await targetEl.screenshot({
          path: outputPath,
          type: "webp",
          quality: 85
        });
      } else {
        // Fallback: clip viewport
        await page.screenshot({
          path: outputPath,
          type: "webp",
          quality: 85,
          clip: { x: 0, y: 60, width: 1200, height: 600 }
        });
      }

      count++;
      console.log(`[${count}/${files.length}] Captured: assets/thumbnails/${id}.webp`);
    } catch (err) {
      console.error(`Failed to capture ${file}:`, err.message);
    }
  }

  await browser.close();
  console.log(`Successfully captured ${count} template screenshots!`);
}

captureAll().catch(err => {
  console.error("Fatal error:", err);
  process.exit(1);
});
