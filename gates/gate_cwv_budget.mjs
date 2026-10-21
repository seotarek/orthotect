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
 * Validates CSS aspect-ratio property value against W3C CSS Box Sizing Level 4.
 * Syntax: auto || <ratio>
 * where <ratio> = <positive-number> [ / <positive-number> ]?
 */
export function isValidAspectRatio(styleContent) {
  if (!styleContent || typeof styleContent !== 'string') return false;

  const match = styleContent.match(/\baspect-ratio\s*:\s*([^;]+)/i);
  if (!match) return false;

  const rawVal = match[1].trim();
  // Strip optional 'auto' keyword (CSS Box Sizing: 'auto 16/9' or '16/9 auto')
  let val = rawVal.replace(/^\bauto\b\s*/i, '').replace(/\s*\bauto\b$/i, '').trim();
  if (!val) {
    // 'auto' alone does not provide a fixed aspect-ratio to prevent layout shift
    return false;
  }

  // Ratio format: <positive-number> [ / <positive-number> ]?
  const ratioMatch = val.match(/^([0-9]*\.?[0-9]+)\s*(?:\/\s*([0-9]*\.?[0-9]+))?$/);
  if (!ratioMatch) return false;

  const w = parseFloat(ratioMatch[1]);
  const h = ratioMatch[2] !== undefined ? parseFloat(ratioMatch[2]) : 1.0;

  return !isNaN(w) && !isNaN(h) && w > 0 && h > 0;
}

/**
 * Standards-compliant, stack-based HTML DOM depth calculator.
 * - Safely handles attributes with quoted '<' or '>' characters.
 * - Matches open and close tags via a strict LIFO stack.
 * - Accounts for HTML5 void elements.
 * - Strips comments, DOCTYPE, <script>, and <style> blocks.
 */
export function calculateMaxDomDepth(htmlContent, filePath = 'snippet') {
  const voidTags = new Set([
    'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input',
    'link', 'meta', 'param', 'source', 'track', 'wbr'
  ]);

  // Clean comments, doctype, and internal script/style contents
  const cleaned = htmlContent
    .replace(/<!--[\s\S]*?-->/g, '')
    .replace(/<!doctype[^>]*>/gi, '')
    .replace(/<script\b[^>]*>([\s\S]*?)<\/script>/gi, '')
    .replace(/<style\b[^>]*>([\s\S]*?)<\/style>/gi, '');

  let maxDepth = 0;
  const tagStack = [];

  let i = 0;
  const len = cleaned.length;

  while (i < len) {
    if (cleaned[i] === '<') {
      // Find end of tag while respecting quoted strings
      let j = i + 1;
      let inQuote = null;
      let tagClosed = false;

      while (j < len) {
        const char = cleaned[j];
        if (inQuote) {
          if (char === inQuote) {
            inQuote = null; // Quote closed
          }
        } else if (char === '"' || char === "'") {
          inQuote = char; // Quote opened
        } else if (char === '>') {
          tagClosed = true;
          break;
        }
        j++;
      }

      if (!tagClosed) {
        // Unclosed tag syntax
        break;
      }

      const tagContent = cleaned.slice(i + 1, j).trim();
      i = j + 1;

      if (!tagContent) continue;

      const isClosing = tagContent.startsWith('/');
      const isSelfClosing = tagContent.endsWith('/');

      let rawName = isClosing ? tagContent.slice(1).trim() : tagContent;
      // Extract tag name before whitespace or slash
      const nameMatch = rawName.match(/^([a-zA-Z0-9-]+)/);
      if (!nameMatch) continue;

      const tagName = nameMatch[1].toLowerCase();

      if (voidTags.has(tagName) || isSelfClosing) {
        continue;
      }

      if (isClosing) {
        if (tagStack.length > 0) {
          const topTag = tagStack[tagStack.length - 1];
          if (topTag === tagName) {
            tagStack.pop();
          } else {
            // Mismatched closing tag detected: search stack for matching open tag
            const idx = tagStack.lastIndexOf(tagName);
            if (idx !== -1) {
              // Pop down to the matching tag
              tagStack.splice(idx);
            } else {
              // Unmatched closing tag
              errors.push(`${filePath}: Malformed HTML - unmatched closing tag </${tagName}>.`);
            }
          }
        } else {
          errors.push(`${filePath}: Malformed HTML - stray closing tag </${tagName}> without open tag.`);
        }
      } else {
        tagStack.push(tagName);
        if (tagStack.length > maxDepth) {
          maxDepth = tagStack.length;
        }
      }
    } else {
      i++;
    }
  }

  return maxDepth;
}

function checkHtmlFile(filePath) {
  const content = fs.readFileSync(filePath, 'utf-8');
  checkedFiles++;

  // 1. Strict image dimension check:
  // Requires BOTH width and height attributes OR a mathematically valid inline CSS aspect-ratio property.
  const imgRegex = /<img\s+([^>]*?)>/gi;
  let match;
  while ((match = imgRegex.exec(content)) !== null) {
    const attrs = match[1];
    const hasWidth = /\bwidth\s*=/i.test(attrs);
    const hasHeight = /\bheight\s*=/i.test(attrs);

    // Strict aspect-ratio check: MUST be a declared and valid CSS property in the style attribute
    const styleMatch = attrs.match(/\bstyle\s*=\s*["']([^"']*)["']/i);
    const styleContent = styleMatch ? styleMatch[1] : '';
    const hasValidAspect = isValidAspectRatio(styleContent);
    const hasBothDimensions = hasWidth && hasHeight;

    if (!hasBothDimensions && !hasValidAspect) {
      if (/\baspect-ratio\b/i.test(styleContent)) {
        errors.push(`${filePath}: <img> has invalid CSS aspect-ratio value in style attribute ("${styleContent}"). Must be a positive ratio like "16/9" or "1".`);
      } else {
        errors.push(`${filePath}: <img> tag lacks complete dimensions (requires BOTH width and height attributes, or a valid inline CSS aspect-ratio property to prevent CLS layout shift).`);
      }
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

  // 3. DOM nesting depth limit (< 32 levels) using stack parser
  const maxDepth = calculateMaxDomDepth(content, filePath);
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
