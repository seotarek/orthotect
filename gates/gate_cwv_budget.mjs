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
 * Parses raw HTML tag attribute string into an object dictionary.
 * Prevents confusion between 'width' and 'data-width'.
 */
export function parseHtmlAttributes(attrsStr) {
  if (!attrsStr || typeof attrsStr !== 'string') return {};
  const attrs = {};
  const regex = /([a-zA-Z0-9_:-]+)(?:\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s"'=<>`]+)))?/g;
  let match;
  while ((match = regex.exec(attrsStr)) !== null) {
    const attrName = match[1].toLowerCase();
    const val = match[2] !== undefined ? match[2] : (match[3] !== undefined ? match[3] : (match[4] !== undefined ? match[4] : ""));
    attrs[attrName] = val;
  }
  return attrs;
}

/**
 * Validates whether an HTML width/height attribute value is a positive number.
 * Accepts "200", "200px", "150.5".
 * Rejects "0", "-100", "", "invalid", "auto", "100%".
 */
export function isPositiveDimension(val) {
  if (val === undefined || val === null || typeof val !== 'string') return false;
  const clean = val.trim().replace(/px$/i, '').trim();
  if (!clean) return false;
  if (!/^[0-9]+(?:\.[0-9]+)?$/.test(clean)) return false;
  const num = parseFloat(clean);
  return !isNaN(num) && num > 0;
}

/**
 * Parses a CSS style string into an object of declared properties.
 * Handles quoted strings and semicolons properly.
 */
export function parseStyleDeclarations(styleStr) {
  if (!styleStr || typeof styleStr !== 'string') return {};
  const decls = {};
  let current = '';
  let inQuote = null;

  for (let i = 0; i < styleStr.length; i++) {
    const ch = styleStr[i];
    if (inQuote) {
      if (ch === inQuote) inQuote = null;
      current += ch;
    } else if (ch === '"' || ch === "'") {
      inQuote = ch;
      current += ch;
    } else if (ch === ';') {
      const colonIdx = current.indexOf(':');
      if (colonIdx > 0) {
        const prop = current.slice(0, colonIdx).trim().toLowerCase();
        const val = current.slice(colonIdx + 1).trim();
        decls[prop] = val;
      }
      current = '';
    } else {
      current += ch;
    }
  }
  if (current.trim()) {
    const colonIdx = current.indexOf(':');
    if (colonIdx > 0) {
      const prop = current.slice(0, colonIdx).trim().toLowerCase();
      const val = current.slice(colonIdx + 1).trim();
      decls[prop] = val;
    }
  }
  return decls;
}

/**
 * Validates CSS aspect-ratio property value against W3C CSS Box Sizing Level 4.
 * Syntax: auto || <ratio>
 * where <ratio> = <positive-number> [ / <positive-number> ]?
 */
export function isValidAspectRatioValue(rawVal) {
  if (!rawVal || typeof rawVal !== 'string') return false;

  let val = rawVal.replace(/^\bauto\b\s*/i, '').replace(/\s*\bauto\b$/i, '').trim();
  if (!val) {
    // 'auto' alone does not provide a fixed aspect-ratio to prevent layout shift
    return false;
  }

  const ratioMatch = val.match(/^([0-9]*\.?[0-9]+)\s*(?:\/\s*([0-9]*\.?[0-9]+))?$/);
  if (!ratioMatch) return false;

  const w = parseFloat(ratioMatch[1]);
  const h = ratioMatch[2] !== undefined ? parseFloat(ratioMatch[2]) : 1.0;

  return !isNaN(w) && !isNaN(h) && w > 0 && h > 0;
}

/**
 * Standards-compliant, stack-based HTML DOM depth and structural integrity validator.
 * - Safely handles attributes with quoted '<' or '>' characters.
 * - Matches open and close tags via strict LIFO stack.
 * - Rejects mismatched closing tags and unclosed tags at EOF.
 * - Rejects unclosed '<' opening syntax.
 * - Accounts for HTML5 void elements.
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
      let j = i + 1;
      let inQuote = null;
      let tagClosed = false;

      while (j < len) {
        const char = cleaned[j];
        if (inQuote) {
          if (char === inQuote) inQuote = null;
        } else if (char === '"' || char === "'") {
          inQuote = char;
        } else if (char === '>') {
          tagClosed = true;
          break;
        }
        j++;
      }

      if (!tagClosed) {
        errors.push(`${filePath}: Malformed HTML - unclosed tag opening syntax '<' at position ${i}.`);
        break;
      }

      const tagContent = cleaned.slice(i + 1, j).trim();
      i = j + 1;

      if (!tagContent) continue;

      const isClosing = tagContent.startsWith('/');
      const isSelfClosing = tagContent.endsWith('/');

      let rawName = isClosing ? tagContent.slice(1).trim() : tagContent;
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
            // Strict rejection of mismatched closing tag
            errors.push(`${filePath}: Malformed HTML - mismatched closing tag </${tagName}>, expected </${topTag}>.`);
            const idx = tagStack.lastIndexOf(tagName);
            if (idx !== -1) {
              tagStack.splice(idx);
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

  // Check for unclosed tags remaining on the stack at EOF (excluding optional html/body)
  const unclosed = tagStack.filter(t => t !== 'html' && t !== 'body');
  if (unclosed.length > 0) {
    errors.push(`${filePath}: Malformed HTML - unclosed tag(s) remaining at end of file: <${unclosed.join('>, <')}>.`);
  }

  return maxDepth;
}

function checkHtmlFile(filePath) {
  const content = fs.readFileSync(filePath, 'utf-8');
  checkedFiles++;

  // 1. Strict image dimension check:
  // Requires explicit, valid width and height attributes OR a verified CSS aspect-ratio property declaration.
  const imgRegex = /<img\b([^>]*?)>/gi;
  let match;
  while ((match = imgRegex.exec(content)) !== null) {
    const rawAttrs = match[1];
    const attrs = parseHtmlAttributes(rawAttrs);

    // Exact attribute name check (data-width will NOT match attrs['width'])
    const hasValidWidth = isPositiveDimension(attrs['width']);
    const hasValidHeight = isPositiveDimension(attrs['height']);
    const hasBothDimensions = hasValidWidth && hasValidHeight;

    // Strict aspect-ratio check on parsed style declarations
    const styleDecls = parseStyleDeclarations(attrs['style'] || '');
    let hasValidAspect = false;

    if (Object.prototype.hasOwnProperty.call(styleDecls, 'aspect-ratio')) {
      const aspectVal = styleDecls['aspect-ratio'];
      hasValidAspect = isValidAspectRatioValue(aspectVal);
      if (!hasValidAspect) {
        errors.push(`${filePath}: <img> has invalid CSS aspect-ratio value in style attribute ("${aspectVal}"). Must be a positive ratio (e.g. "16/9" or "1").`);
      }
    }

    if (!hasBothDimensions && !hasValidAspect) {
      if (attrs['data-width'] || attrs['data-height']) {
        errors.push(`${filePath}: <img> uses data-width/data-height instead of native HTML width/height attributes or CSS aspect-ratio.`);
      } else if (!hasValidWidth && 'width' in attrs) {
        errors.push(`${filePath}: <img> has invalid width attribute value ("${attrs['width']}"). Must be a positive number.`);
      } else if (!hasValidHeight && 'height' in attrs) {
        errors.push(`${filePath}: <img> has invalid height attribute value ("${attrs['height']}"). Must be a positive number.`);
      } else {
        errors.push(`${filePath}: <img> tag lacks complete dimensions (requires BOTH width and height attributes, or a valid inline CSS aspect-ratio property to prevent CLS layout shift).`);
      }
    }
  }

  // 2. Blocking synchronous <script> tags in <head>
  const headMatch = content.match(/<head[^>]*>([\s\S]*?)<\/head>/i);
  if (headMatch) {
    const headContent = headMatch[1];
    const scriptRegex = /<script\b([^>]*?)>/gi;
    let sMatch;
    while ((sMatch = scriptRegex.exec(headContent)) !== null) {
      const sAttrs = parseHtmlAttributes(sMatch[1]);
      const isAsync = 'async' in sAttrs;
      const isDefer = 'defer' in sAttrs;
      const isModule = sAttrs['type'] === 'module';
      const isInline = !('src' in sAttrs);
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
