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

function checkHtmlFile(filePath) {
  const content = fs.readFileSync(filePath, 'utf-8');
  checkedFiles++;

  // 1. Unconstrained <img> tags without width/height or aspect-ratio (causes CLS)
  const imgRegex = /<img\s+([^>]*?)>/gi;
  let match;
  while ((match = imgRegex.exec(content)) !== null) {
    const attrs = match[1];
    const hasWidth = /\bwidth\s*=/i.test(attrs);
    const hasHeight = /\bheight\s*=/i.test(attrs);
    const hasAspect = /aspect-ratio/i.test(attrs);
    if (!hasWidth && !hasHeight && !hasAspect) {
      errors.push(`${filePath}: <img> tag lacks explicit width/height or aspect-ratio (triggers CLS layout shift).`);
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

  // 3. DOM nesting depth limit (< 32 levels)
  const lines = content.split('\n');
  let maxDepth = 0;
  let currentDepth = 0;
  for (const line of lines) {
    const opens = (line.match(/<[a-z0-9]+(\s+[^>]*)?>/gi) || []).filter(tag => !tag.startsWith('</') && !tag.endsWith('/>') && !/<(br|hr|img|input|link|meta)/i.test(tag)).length;
    const closes = (line.match(/<\/[a-z0-9]+>/gi) || []).length;
    currentDepth += opens - closes;
    if (currentDepth > maxDepth) maxDepth = currentDepth;
  }

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
