#!/usr/bin/env node
/**
 * Orthotect Gate: Core Web Vitals (CWV) Structural Budget
 * Verifies layout-shift prevention (CLS) and DOM depth limits.
 */
import fs from 'fs';
import path from 'path';

console.log("═══════════════════════════════════════════════════════════════");
console.log("  ORTHOTECT GATE: Core Web Vitals Structural Budget");
console.log("═══════════════════════════════════════════════════════════════");

const targetDir = process.argv[2] || 'examples';
let checkedFiles = 0;
let errors = [];

function checkHtmlFile(filePath) {
  const content = fs.readFileSync(filePath, 'utf-8');
  checkedFiles++;

  // 1. Check for unconstrained img tags without width/height or aspect-ratio
  const imgRegex = /<img\s+([^>]*?)>/gi;
  let match;
  while ((match = imgRegex.exec(content)) !== null) {
    const attrs = match[1];
    const hasWidth = /\bwidth\s*=/i.test(attrs);
    const hasHeight = /\bheight\s*=/i.test(attrs);
    const hasAspect = /aspect-ratio/i.test(attrs);
    if (!hasWidth && !hasHeight && !hasAspect) {
      errors.push(`${filePath}: <img> tag lacks explicit width/height or aspect-ratio (causes CLS)`);
    }
  }

  // 2. Check DOM nesting depth limit (Google threshold < 32)
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
    errors.push(`${filePath}: Excessive DOM depth of ${maxDepth} (Google CWV limit is 32 levels)`);
  }
}

if (fs.existsSync(targetDir)) {
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

if (errors.length === 0) {
  console.log(`\n✅ [PASS] Core Web Vitals checks passed across ${checkedFiles} file(s)!`);
  console.log("   Zero unconstrained layout-shift elements; DOM depth safely within budgets.");
  process.exit(0);
} else {
  console.log(`\n❌ [REJECT] Found ${errors.length} Core Web Vitals budget violation(s):`);
  errors.forEach(e => console.log(`   - ${e}`));
  process.exit(1);
}
