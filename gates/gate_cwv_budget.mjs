#!/usr/bin/env node
/**
 * Orthotect Gate: DOM Structure & Layout-Shift (CLS) Budget
 * Verifies that media elements reserve dimensions and DOM depth stays within bounds.
 */
import fs from 'fs';
import path from 'path';

console.log("═══════════════════════════════════════════════════════════════");
console.log("  ORTHOTECT GATE: DOM Structure & Layout-Shift Budget");
console.log("═══════════════════════════════════════════════════════════════");

const targetDir = process.argv[2] || 'examples';
if (!fs.existsSync(targetDir)) {
  console.error(`❌ [REJECT] Target path not found: ${targetDir}`);
  process.exit(1);
}

let checkedFiles = 0;
let errors = [];

/**
 * Sequential stream-based DOM depth calculator.
 * Accurately parses minified single-line HTML, nested multi-line HTML,
 * and correctly handles void elements (<br>, <img>, <input>, <meta>, etc.).
 */
function calculateMaxDomDepth(htmlContent) {
  const voidTags = new Set([
    'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 
    'link', 'meta', 'param', 'source', 'track', 'wbr'
  ]);
  
  // Clean comments and doctype
  const cleaned = htmlContent
    .replace(/<!--[\s\S]*?-->/g, '')
    .replace(/<!doctype[^>]*>/gi, '');

  const tagRegex = /<(\/)?([a-z0-9-]+)(\s+[^>]*)?(\/)?>/gi;
  let maxDepth = 0;
  let currentDepth = 0;
  let match;

  while ((match = tagRegex.exec(cleaned)) !== null) {
    const isClosing = Boolean(match[1]);
    const tagName = match[2].toLowerCase();
    const isSelfClosing = Boolean(match[4]);

    if (voidTags.has(tagName) || isSelfClosing) {
      continue;
    }

    if (isClosing) {
      if (currentDepth > 0) currentDepth--;
    } else {
      currentDepth++;
      if (currentDepth > maxDepth) maxDepth = currentDepth;
    }
  }

  return maxDepth;
}

function checkHtmlFile(filePath) {
  const content = fs.readFileSync(filePath, 'utf-8');
  checkedFiles++;

  // 1. Strict image dimension check:
  // Requires BOTH width and height attributes (so browser can calculate aspect-ratio) OR explicit CSS aspect-ratio.
  const imgRegex = /<img\s+([^>]*?)>/gi;
  let match;
  while ((match = imgRegex.exec(content)) !== null) {
    const attrs = match[1];
    const hasWidth = /\bwidth\s*=/i.test(attrs);
    const hasHeight = /\bheight\s*=/i.test(attrs);
    const hasAspect = /aspect-ratio/i.test(attrs);
    const hasBothDimensions = hasWidth && hasHeight;

    if (!hasBothDimensions && !hasAspect) {
      errors.push(`${filePath}: <img> tag lacks complete dimensions (requires BOTH width and height attributes, or an explicit aspect-ratio to prevent CLS layout shift).`);
    }
  }

  // 2. Blocking synchronous <script> tags in <head>
  const headMatch = content.match(/<head[^>]*>([\s\S]*?)<\/head>/i);
  if (headMatch) {
    const headContent = headMatch[1];
    const scriptRegex = /<script\s+([^>]*?)>/gi;
    let sMatch;
    while ((sMatch = scriptRegex.exec(headContent)) !== null) {
      const sAttrs = sMatch[1];
      const isAsync = /\basync\b/i.test(sAttrs);
      const isDefer = /\bdefer\b/i.test(sAttrs);
      const isModule = /type=["']module["']/i.test(sAttrs);
      const isInline = !/\bsrc\s*=/i.test(sAttrs);
      if (!isInline && !isAsync && !isDefer && !isModule) {
        errors.push(`${filePath}: Synchronous blocking <script> in <head> without defer/async.`);
      }
    }
  }

  // 3. DOM nesting depth limit (< 32 levels) using stream parser
  const maxDepth = calculateMaxDomDepth(content);
  if (maxDepth > 32) {
    errors.push(`${filePath}: Excessive DOM depth of ${maxDepth} levels (Budget max is 32).`);
  }
}

if (fs.statSync(targetDir).isFile() && targetDir.endsWith('.html')) {
  checkHtmlFile(targetDir);
} else {
  const scan = (dir) => {
    for (const f of fs.readdirSync(dir)) {
      const full = path.join(dir, f);
      if (fs.statSync(full).isDirectory()) {
        if (!['node_modules', '.git', 'dist'].includes(f)) scan(full);
      } else if (f.endsWith('.html')) {
        checkHtmlFile(full);
      }
    }
  };
  scan(targetDir);
}

if (checkedFiles === 0) {
  console.log(`\n❌ [REJECT] No markup (.html) files found to inspect in: ${targetDir}`);
  console.log("   Orthotect requires markup files to verify DOM budgets and CLS avoidance.");
  process.exit(1);
}

if (errors.length === 0) {
  console.log(`\n✅ [PASS] Layout-Shift & DOM budgets passed across ${checkedFiles} file(s)!`);
  process.exit(0);
} else {
  console.log(`\n❌ [REJECT] Found ${errors.length} structural budget violation(s):`);
  errors.forEach(e => console.log(`   - ${e}`));
  process.exit(1);
}
