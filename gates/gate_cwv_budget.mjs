#!/usr/bin/env node
/**
 * Orthotect Gate: DOM Structure & Layout-Shift (CLS) Budget
 * Verifies that media elements reserve dimensions and DOM depth stays within bounds.
 */
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

import * as parse5 from 'parse5';

const isMain = process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url);

let targetDir = 'examples';
if (isMain) {
  console.log("═══════════════════════════════════════════════════════════════");
  console.log("  ORTHOTECT GATE: DOM Structure & Layout-Shift Budget");
  console.log("═══════════════════════════════════════════════════════════════");
  targetDir = process.argv[2] || 'examples';
  if (!fs.existsSync(targetDir)) {
    console.error(`❌ [REJECT] Target path not found: ${targetDir}`);
    process.exit(1);
  }
}

let checkedFiles = 0;
let errors = [];

/**
 * Parses raw HTML tag attribute string into an object dictionary.
 * Prevents confusion between 'width' and 'data-width'.
 * Preserves quotes containing '<' or '>'.
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
 * Validates whether an HTML width/height attribute value is a valid positive integer.
 * Per HTML5 specification (§ 4.8.4.1.3 Dimension attributes), width/height on <img>
 * must be valid non-negative integers (ASCII digits only, no 'px', no decimals, no signs).
 * Accepts "200", "800".
 * Rejects "200px", "0", "-100", "", "invalid", "auto", "100%", "150.5".
 */
export function isPositiveDimension(val) {
  if (val === undefined || val === null || typeof val !== 'string') return false;
  const clean = val.trim();
  if (!clean) return false;
  if (!/^[1-9]\d*$/.test(clean)) return false;
  const num = parseInt(clean, 10);
  return !isNaN(num) && num > 0;
}

/**
 * Parses a CSS style string into an object of declared properties.
 * Handles quoted strings, strips CSS comments, and handles repeated declarations.
 */
export function parseStyleDeclarations(styleStr) {
  if (!styleStr || typeof styleStr !== 'string') return {};
  const stripped = styleStr.replace(/\/\*[\s\S]*?\*\//g, '');
  const decls = {};
  let current = '';
  let inQuote = null;

  for (let i = 0; i < stripped.length; i++) {
    const ch = stripped[i];
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
        if (prop) decls[prop] = val;
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
      if (prop) decls[prop] = val;
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
  val = val.replace(/\s*!important\s*$/i, '').trim();
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
 * Parses, type-checks per W3C CSS Values and Units Level 4 (§ 8.1.1),
 * validates parenthesis matching, and mathematically evaluates CSS calc() expressions.
 * Enforces:
 * - Balanced parentheses (rejects unbalanced ( or ))
 * - Multiplication requires at least one unitless <number> operand (rejects length * length)
 * - Addition/subtraction operands must match types (rejects length + number)
 * - Division right operand must be a non-zero unitless <number> (rejects length / length, length / 0)
 * - Dimension expression must resolve to <length> (rejects unitless numbers)
 * - All evaluated reference models (mobile, desktop, neutral) must be strictly positive (> 0)
 */
export function parseAndValidateCssCalc(innerStr) {
  if (!innerStr || typeof innerStr !== 'string') return false;
  const str = innerStr.trim();
  if (!str) return false;

  const validUnits = new Set(['px', 'rem', 'em', 'vw', 'vh', '%', 'cqi', 'cqw', 'pt', 'cm', 'mm', 'in', 'vmin', 'vmax', 'ch', 'ex']);
  const numberRegex = /^[+-]?(?:[0-9]+(?:\.[0-9]+)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?$/;

  // 1. Lexical Tokenization
  const tokens = [];
  let i = 0;
  const len = str.length;
  while (i < len) {
    const ch = str[i];
    if (/\s/.test(ch)) {
      i++;
      continue;
    }
    if (ch === '(' || ch === ')' || ch === '*' || ch === '/') {
      tokens.push({ type: ch, raw: ch });
      i++;
      continue;
    }
    if (ch === '+' || ch === '-') {
      const prev = tokens.length > 0 ? tokens[tokens.length - 1].type : null;
      const isUnary = !prev || prev === '(' || prev === '+' || prev === '-' || prev === '*' || prev === '/';
      if (isUnary) {
        // In CSS Syntax Level 3, a unary sign must be followed immediately by a number (or opening parenthesis)
        // with ZERO whitespace! (e.g. "-10px", not "- 10px")
        const nextChar = str[i + 1];
        if (!nextChar || /\s/.test(nextChar)) {
          return false; // Space after unary sign is INVALID in CSS
        }

        if (nextChar === '(') {
          tokens.push({ type: 'unary', sign: ch === '-' ? -1 : 1 });
          i++;
          continue;
        }

        if (/[0-9.]/.test(nextChar)) {
          const sign = ch === '-' ? -1 : 1;
          i++; // consume sign
          const numStart = i;
          while (i < len && /[0-9.]/.test(str[i])) i++;
          // W3C CSS Syntax Module Level 3 (§ 4.3.12 Consume a number):
          // An exponent indicator 'e' or 'E' is only part of the number if followed by an optional sign and at least one digit!
          // This strictly avoids colliding with valid CSS units such as 'em' and 'ex' (e.g. "10em", "10ex").
          if (i < len && (str[i] === 'e' || str[i] === 'E')) {
            const rem = str.slice(i);
            const expMatch = rem.match(/^[eE][+-]?[0-9]+/);
            if (expMatch) {
              i += expMatch[0].length;
            }
          }
          const rawNum = str.slice(numStart, i);
          if (!numberRegex.test(rawNum)) {
            return false;
          }
          const numVal = parseFloat(rawNum);
          if (isNaN(numVal)) return false;

          const unitStart = i;
          while (i < len && /[a-zA-Z%]/.test(str[i])) i++;
          const unit = str.slice(unitStart, i).toLowerCase();
          if (unit && !validUnits.has(unit)) return false;

          tokens.push({
            type: 'val',
            num: sign * numVal,
            unit: unit || null,
            dimType: unit ? 'length' : 'number'
          });
          continue;
        }
        return false;
      } else {
        // Binary infix operator "+" or "-": W3C CSS Values and Units Level 4 (§ 8.1.1) requires whitespace on BOTH sides!
        const hasPrecedingSpace = i > 0 && /\s/.test(str[i - 1]);
        const hasFollowingSpace = (i + 1 < len) && /\s/.test(str[i + 1]);
        if (!hasPrecedingSpace || !hasFollowingSpace) {
          return false;
        }
        tokens.push({ type: ch, raw: ch });
        i++;
        continue;
      }
    }
    if (/[0-9.]/.test(ch)) {
      const numStart = i;
      while (i < len && /[0-9.]/.test(str[i])) i++;
      // W3C CSS Syntax Module Level 3 (§ 4.3.12 Consume a number):
      // An exponent indicator 'e' or 'E' is only part of the number if followed by an optional sign and at least one digit!
      // This strictly avoids colliding with valid CSS units such as 'em' and 'ex' (e.g. "10em", "10ex").
      if (i < len && (str[i] === 'e' || str[i] === 'E')) {
        const rem = str.slice(i);
        const expMatch = rem.match(/^[eE][+-]?[0-9]+/);
        if (expMatch) {
          i += expMatch[0].length;
        }
      }
      const rawNum = str.slice(numStart, i);
      if (!numberRegex.test(rawNum)) {
        return false;
      }
      const numVal = parseFloat(rawNum);
      if (isNaN(numVal)) return false;
      const unitStart = i;
      while (i < len && /[a-zA-Z%]/.test(str[i])) i++;
      const unit = str.slice(unitStart, i).toLowerCase();
      if (unit && !validUnits.has(unit)) return false;
      tokens.push({
        type: 'val',
        num: numVal,
        unit: unit || null,
        dimType: unit ? 'length' : 'number'
      });
      continue;
    }
    // Unrecognized character
    return false;
  }

  if (tokens.length === 0) return false;

  // 2. Recursive-Descent Parser with W3C CSS Values and Units Level 4 (§ 8.1.1) Type Checking
  let pos = 0;

  function parseFactor() {
    if (pos >= tokens.length) return null;
    let sign = 1;
    if (tokens[pos].type === 'unary') {
      sign = tokens[pos].sign;
      pos++;
      if (pos >= tokens.length) return null;
    } else if (tokens[pos].type === '+' || tokens[pos].type === '-') {
      if (tokens[pos].type === '-') sign = -1;
      pos++;
      if (pos >= tokens.length) return null;
    }

    const t = tokens[pos];
    if (t.type === '(') {
      pos++; // consume (
      const expr = parseExpression();
      if (!expr) return null;
      if (pos >= tokens.length || tokens[pos].type !== ')') {
        // Unbalanced opening parenthesis: missing closing ')'
        return null;
      }
      pos++; // consume )
      return {
        dimType: expr.dimType,
        evalNode: (map) => sign * expr.evalNode(map)
      };
    }

    if (t.type === 'val') {
      pos++; // consume val
      const valToken = t;
      return {
        dimType: valToken.dimType,
        evalNode: (map) => {
          const factor = valToken.unit ? (map[valToken.unit] !== undefined ? map[valToken.unit] : 1) : 1;
          return sign * valToken.num * factor;
        }
      };
    }

    return null;
  }

  function parseTerm() {
    let left = parseFactor();
    if (!left) return null;

    while (pos < tokens.length && (tokens[pos].type === '*' || tokens[pos].type === '/')) {
      const op = tokens[pos].type;
      pos++;
      const right = parseFactor();
      if (!right) return null;

      if (op === '*') {
        // W3C Rule: At least one operand must be a <number>
        if (left.dimType === 'length' && right.dimType === 'length') {
          return null; // Cannot multiply length by length
        }
        const resDimType = (left.dimType === 'length' || right.dimType === 'length') ? 'length' : 'number';
        const prevLeft = left;
        left = {
          dimType: resDimType,
          evalNode: (map) => prevLeft.evalNode(map) * right.evalNode(map)
        };
      } else {
        // Division: Right operand MUST be a unitless <number>
        if (right.dimType !== 'number') {
          return null; // Cannot divide by length or dimension
        }
        const prevLeft = left;
        left = {
          dimType: prevLeft.dimType, // preserves left type
          evalNode: (map) => {
            const rVal = right.evalNode(map);
            if (rVal === 0) return NaN;
            return prevLeft.evalNode(map) / rVal;
          }
        };
      }
    }
    return left;
  }

  function parseExpression() {
    let left = parseTerm();
    if (!left) return null;

    while (pos < tokens.length && (tokens[pos].type === '+' || tokens[pos].type === '-')) {
      const op = tokens[pos].type;
      pos++;
      const right = parseTerm();
      if (!right) return null;

      // W3C Rule: Both operands must have matching types (length + length, or number + number)
      if (left.dimType !== right.dimType) {
        return null; // Cannot add/subtract length and unitless number
      }

      const prevLeft = left;
      left = {
        dimType: prevLeft.dimType,
        evalNode: (map) => {
          const lVal = prevLeft.evalNode(map);
          const rVal = right.evalNode(map);
          return op === '+' ? lVal + rVal : lVal - rVal;
        }
      };
    }
    return left;
  }

  const ast = parseExpression();
  if (!ast) return false;

  // Unconsumed tokens (e.g. extra closing parenthesis or invalid trailing token)
  if (pos < tokens.length) return false;

  // A CSS dimension (width/height) MUST resolve to <length> (or percentage), NOT a unitless number
  if (ast.dimType !== 'length') return false;

  // 3. Dimensional Evaluation across mobile, desktop, and neutral models
  const mobileMap = { px: 1, rem: 16, em: 16, vw: 3.6, vh: 6.4, '%': 3.6, cqi: 3.6, cqw: 3.6, pt: 1.333, cm: 37.795, mm: 3.7795, in: 96, vmin: 3.6, vmax: 6.4, ch: 8, ex: 8 };
  const desktopMap = { px: 1, rem: 16, em: 16, vw: 14.4, vh: 9.0, '%': 14.4, cqi: 14.4, cqw: 14.4, pt: 1.333, cm: 37.795, mm: 3.7795, in: 96, vmin: 9.0, vmax: 14.4, ch: 8, ex: 8 };
  const neutralMap = { px: 1, rem: 1, em: 1, vw: 1, vh: 1, '%': 1, cqi: 1, cqw: 1, pt: 1, cm: 1, mm: 1, in: 1, vmin: 1, vmax: 1, ch: 1, ex: 1 };

  const mVal = ast.evalNode(mobileMap);
  const dVal = ast.evalNode(desktopMap);
  const nVal = ast.evalNode(neutralMap);

  if (isNaN(mVal) || isNaN(dVal) || isNaN(nVal)) return false;
  return mVal > 0 && dVal > 0 && nVal > 0;
}

/**
 * Validates CSS dimension property value (width/height).
 * Rejects 'auto', 'none', 'initial', 'inherit', 'unset', '0', '0px', and any invalid or non-positive calc().
 * Accepts positive dimensions with length/percentage units or mathematically positive valid calc().
 */
export function isValidCssDimensionValue(val) {
  if (!val || typeof val !== 'string') return false;
  const clean = val.trim().toLowerCase().replace(/\s*!important\s*$/i, '').trim();
  if (['auto', 'none', 'initial', 'inherit', 'unset', '0', '0px', ''].includes(clean)) return false;

  // Single length/percentage dimension check: e.g. "200px", "50%", "10rem", "10em", "10ex"
  const directMatch = clean.match(/^([1-9]\d*(?:\.\d+)?)(px|rem|em|vw|vh|%|cqi|cqw|pt|cm|mm|in|vmin|vmax|ch|ex)$/i);
  if (directMatch) return true;

  // Calc expression evaluation
  const calcMatch = clean.match(/^calc\((.+)\)$/i);
  if (!calcMatch) return false;

  const inner = calcMatch[1].trim();
  if (!inner) return false;

  return parseAndValidateCssCalc(inner);
}

/**
 * Standards-compliant HTML5 DOM depth calculator and structural validator using parse5.
 * - Handles minified and multiline HTML.
 * - Accurately accounts for HTML5 void elements, comments, scripts, styles.
 * - Rejects non-void elements with trailing solidus (e.g. <div/> is not self-closing).
 * - Detects unclosed tag syntax at EOF (<span class=).
 * - Detects unclosed non-void tags remaining at EOF (<section><p>).
 * - Detects mismatched closing tags.
 */
export function calculateMaxDomDepth(htmlContent, filePath = 'snippet') {
  const voidTags = new Set([
    'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input',
    'link', 'meta', 'param', 'source', 'track', 'wbr'
  ]);
  const optionalClosing = new Set([
    'html', 'body', 'p', 'li', 'td', 'tr', 'dt', 'dd', 'option', 'thead', 'tbody', 'tfoot'
  ]);

  // 1. WHATWG HTML5 AST parsing with parse5
  const parseErrors = [];
  const doc = parse5.parse(htmlContent, {
    sourceCodeLocationInfo: true,
    onParseError: (err) => parseErrors.push(err)
  });

  for (const pe of parseErrors) {
    if (pe.code === 'eof-in-tag' || pe.code === 'eof-before-tag-name' || pe.code === 'eof-in-attribute-value') {
      errors.push(`${filePath}: Malformed HTML - unclosed tag opening or attribute syntax '<' at position ${pe.startOffset || 0}.`);
    } else if (pe.code === 'non-void-html-element-start-tag-with-trailing-solidus') {
      errors.push(`${filePath}: Malformed HTML - non-void HTML element start tag with trailing solidus (<div/> is not self-closing in HTML5).`);
    } else if (pe.code === 'end-tag-without-matching-open-element') {
      errors.push(`${filePath}: Malformed HTML - stray or mismatched closing tag without matching open element.`);
    } else if (pe.code === 'duplicate-attribute') {
      errors.push(`${filePath}: Malformed HTML - duplicate attribute on element.`);
    }
  }

  // 2. Tokenizer structural stack validation for unclosed non-optional tags & mismatched tags
  const stack = [];
  const tokenizer = new parse5.Tokenizer({}, {
    onNullCharacter: () => {},
    onWhitespaceCharacter: () => {},
    onCharacter: () => {},
    onComment: () => {},
    onDoctype: () => {},
    onStartTag: (t) => {
      if (!voidTags.has(t.tagName) && !t.selfClosing) {
        stack.push(t.tagName);
      }
    },
    onEndTag: (t) => {
      if (voidTags.has(t.tagName)) return;
      if (stack.length === 0) {
        errors.push(`${filePath}: Malformed HTML - stray closing tag </${t.tagName}> without open tag.`);
        return;
      }
      const top = stack[stack.length - 1];
      if (top === t.tagName) {
        stack.pop();
      } else {
        while (stack.length > 0 && optionalClosing.has(stack[stack.length - 1]) && stack[stack.length - 1] !== t.tagName) {
          stack.pop();
        }
        if (stack.length > 0 && stack[stack.length - 1] === t.tagName) {
          stack.pop();
        } else {
          errors.push(`${filePath}: Malformed HTML - mismatched closing tag </${t.tagName}>, expected </${top}>.`);
          const idx = stack.lastIndexOf(t.tagName);
          if (idx !== -1) stack.splice(idx);
        }
      }
    },
    onEof: () => {}
  });

  tokenizer.write(htmlContent, true);

  const unclosed = stack.filter(t => !optionalClosing.has(t));
  if (unclosed.length > 0) {
    errors.push(`${filePath}: Malformed HTML - unclosed tag(s) remaining at end of file: <${unclosed.join('>, <')}>.`);
  }

  // 3. Iterative Tree Depth Calculation from the parsed HTML5 AST using an explicit stack
  let maxTreeDepth = 0;
  let nodesVisited = 0;
  const MAX_NODE_VISIT_LIMIT = 200000;
  const traversalStack = [{ node: doc, depth: 0 }];

  while (traversalStack.length > 0) {
    const { node, depth } = traversalStack.pop();
    nodesVisited++;

    if (nodesVisited > MAX_NODE_VISIT_LIMIT) {
      errors.push(`${filePath}: Resource limit exceeded during AST traversal (> ${MAX_NODE_VISIT_LIMIT} nodes visited). Adversarial DOM structure rejected.`);
      break;
    }

    const isElem = node.nodeName && !node.nodeName.startsWith('#');
    const currentDepth = isElem ? depth + 1 : depth;

    if (currentDepth > maxTreeDepth) {
      maxTreeDepth = currentDepth;
    }

    if (node.childNodes && node.childNodes.length > 0) {
      for (let i = node.childNodes.length - 1; i >= 0; i--) {
        const child = node.childNodes[i];
        if (child.nodeName && !child.nodeName.startsWith('#')) {
          traversalStack.push({ node: child, depth: currentDepth });
        }
      }
    }
  }

  return maxTreeDepth;
}

function findElements(rootNode, tagName) {
  const results = [];
  const stack = [rootNode];
  while (stack.length > 0) {
    const node = stack.pop();
    if (node.nodeName === tagName) results.push(node);
    if (node.childNodes && node.childNodes.length > 0) {
      for (let i = node.childNodes.length - 1; i >= 0; i--) {
        stack.push(node.childNodes[i]);
      }
    }
  }
  return results;
}

export function extractCssRulesFromHtmlAndLinkedSheets(htmlContent, htmlFilePath) {
  const cssTexts = [];
  const styleRegex = /<style\b[^>]*>([\s\S]*?)<\/style>/gi;
  let match;
  while ((match = styleRegex.exec(htmlContent)) !== null) {
    cssTexts.push(match[1]);
  }
  // Robust link tag extraction using parseHtmlAttributes (order-agnostic)
  const linkTagRegex = /<link\b([^>]*)\/?>/gi;
  const dir = path.dirname(htmlFilePath);
  while ((match = linkTagRegex.exec(htmlContent)) !== null) {
    const attrs = parseHtmlAttributes(match[1]);
    if (attrs['rel'] && attrs['rel'].toLowerCase() === 'stylesheet' && attrs['href']) {
      const href = attrs['href'].split('?')[0].split('#')[0];
      const fullPath = path.resolve(dir, href);
      if (fs.existsSync(fullPath)) {
        try {
          cssTexts.push(fs.readFileSync(fullPath, 'utf-8'));
        } catch (_) {}
      }
    }
  }
  return cssTexts.join('\n');
}

export function parseCssSelectorRules(cssText) {
  const selectorMap = {};
  if (!cssText) return selectorMap;
  const stripped = cssText.replace(/\/\*[\s\S]*?\*\//g, '');
  const ruleRegex = /([^{}]+)\{([^{}]+)\}/g;
  let match;
  while ((match = ruleRegex.exec(stripped)) !== null) {
    const selectors = match[1].split(',').map(s => s.trim().toLowerCase());
    const decls = parseStyleDeclarations(match[2]);
    for (const sel of selectors) {
      if (!selectorMap[sel]) selectorMap[sel] = {};
      Object.assign(selectorMap[sel], decls);
    }
  }
  return selectorMap;
}

export function elementMatchesCompound(node, compound) {
  if (!node || !node.nodeName || node.nodeName.startsWith('#')) return false;
  const attrs = {};
  for (const a of (node.attrs || [])) {
    attrs[a.name.toLowerCase()] = a.value;
  }
  const classes = new Set((attrs['class'] || '').toLowerCase().split(/\s+/).filter(Boolean));
  const id = (attrs['id'] || '').toLowerCase();
  const tag = node.nodeName.toLowerCase();

  const parts = compound.match(/^([a-zA-Z0-9_-]+|\*)?((?:\.[a-zA-Z0-9_-]+|#[a-zA-Z0-9_-]+)*)$/);
  if (!parts) return false;
  const [_, tagPart, rest] = parts;
  if (tagPart && tagPart !== '*' && tagPart.toLowerCase() !== tag) return false;

  if (rest) {
    const tokens = rest.match(/([.#][a-zA-Z0-9_-]+)/g) || [];
    for (const tok of tokens) {
      if (tok.startsWith('.')) {
        if (!classes.has(tok.slice(1).toLowerCase())) return false;
      } else if (tok.startsWith('#')) {
        if (id !== tok.slice(1).toLowerCase()) return false;
      }
    }
  }
  return true;
}

export function matchesSelectorChain(node, ancestors, selectorStr) {
  const normalized = selectorStr.replace(/\s*>\s*/g, ' > ').trim().toLowerCase();
  const tokens = normalized.split(/\s+/);
  let currIdx = tokens.length - 1;
  const targetCompound = tokens[currIdx];
  if (!elementMatchesCompound(node, targetCompound)) return false;
  if (tokens.length === 1) return true;

  currIdx--;
  let ancestorIdx = ancestors.length - 1;
  while (currIdx >= 0) {
    if (tokens[currIdx] === '>') {
      currIdx--;
      if (currIdx < 0 || ancestorIdx < 0) return false;
      const parentCompound = tokens[currIdx];
      if (!elementMatchesCompound(ancestors[ancestorIdx], parentCompound)) return false;
      ancestorIdx--;
      currIdx--;
    } else {
      const ancestorCompound = tokens[currIdx];
      let matched = false;
      while (ancestorIdx >= 0) {
        if (elementMatchesCompound(ancestors[ancestorIdx], ancestorCompound)) {
          matched = true;
          ancestorIdx--;
          break;
        }
        ancestorIdx--;
      }
      if (!matched) return false;
      currIdx--;
    }
  }
  return true;
}

export function findElementsWithAncestors(rootNode, tagNames) {
  const targetTags = new Set(tagNames.map(t => t.toLowerCase()));
  const results = [];
  const stack = [{ node: rootNode, ancestors: [] }];
  while (stack.length > 0) {
    const { node, ancestors } = stack.pop();
    if (node.nodeName && targetTags.has(node.nodeName.toLowerCase())) {
      results.push({ node, ancestors });
    }
    if (node.childNodes && node.childNodes.length > 0) {
      const isElem = node.nodeName && !node.nodeName.startsWith('#');
      const nextAncestors = isElem ? [...ancestors, node] : ancestors;
      for (let i = node.childNodes.length - 1; i >= 0; i--) {
        stack.push({ node: node.childNodes[i], ancestors: nextAncestors });
      }
    }
  }
  return results;
}

function checkHtmlFile(filePath) {
  const content = fs.readFileSync(filePath, 'utf-8');
  checkedFiles++;

  if (!content || !content.trim() || !content.replace(/<!--[\s\S]*?-->/g, '').trim()) {
    errors.push(`${filePath}: Empty or non-scannable HTML file (empty, whitespace-only, or comment-only). Orthotect requires valid markup to verify DOM and layout budgets.`);
    return;
  }

  const doc = parse5.parse(content);
  const combinedCss = extractCssRulesFromHtmlAndLinkedSheets(content, filePath);
  const cssRules = parseCssSelectorRules(combinedCss);

  // 1. Strict media dimension check on parsed AST:
  // Inspects <img>, <video>, and <iframe> elements to prevent CLS layout shift.
  const mediaElements = findElementsWithAncestors(doc, ['img', 'video', 'iframe']);
  for (const { node: el, ancestors } of mediaElements) {
    const tag = el.nodeName.toLowerCase();
    const attrs = {};
    for (const a of (el.attrs || [])) {
      attrs[a.name.toLowerCase()] = a.value;
    }

    const hasValidWidth = isPositiveDimension(attrs['width']);
    const hasValidHeight = isPositiveDimension(attrs['height']);
    const hasBothDimensions = hasValidWidth && hasValidHeight;

    const styleDecls = parseStyleDeclarations(attrs['style'] || '');
    let hasValidAspect = false;
    let hasValidCssDims = false;

    // Check inline style aspect-ratio
    if (Object.prototype.hasOwnProperty.call(styleDecls, 'aspect-ratio')) {
      const aspectVal = styleDecls['aspect-ratio'];
      hasValidAspect = isValidAspectRatioValue(aspectVal);
      if (!hasValidAspect) {
        errors.push(`${filePath}: <${tag}> has invalid CSS aspect-ratio value in style attribute ("${aspectVal}"). Must be a positive ratio (e.g. "16/9" or "1").`);
      }
    }

    // Check inline style width and height
    if (Object.prototype.hasOwnProperty.call(styleDecls, 'width') && Object.prototype.hasOwnProperty.call(styleDecls, 'height')) {
      const wVal = styleDecls['width'];
      const hVal = styleDecls['height'];
      if (isValidCssDimensionValue(wVal) && isValidCssDimensionValue(hVal)) {
        hasValidCssDims = true;
      } else if (!hasBothDimensions && !hasValidAspect) {
        errors.push(`${filePath}: <${tag}> has invalid non-reserving CSS dimensions in style ("width: ${wVal}; height: ${hVal}"). Must be positive dimensions with valid units.`);
      }
    }

    // Check external/embedded CSS stylesheet rules matching tag, compound, child, or descendant selectors
    if (!hasBothDimensions && !hasValidAspect && !hasValidCssDims) {
      for (const [selector, ruleDecls] of Object.entries(cssRules)) {
        if (matchesSelectorChain(el, ancestors, selector)) {
          if (ruleDecls['aspect-ratio'] && isValidAspectRatioValue(ruleDecls['aspect-ratio'])) {
            hasValidAspect = true;
            break;
          }
          if (ruleDecls['width'] && ruleDecls['height'] &&
              isValidCssDimensionValue(ruleDecls['width']) && isValidCssDimensionValue(ruleDecls['height'])) {
            hasValidCssDims = true;
            break;
          }
        }
      }
    }

      if (!hasBothDimensions && !hasValidAspect && !hasValidCssDims) {
        if (attrs['data-width'] || attrs['data-height']) {
          errors.push(`${filePath}: <${tag}> uses data-width/data-height instead of native HTML width/height attributes or CSS aspect-ratio.`);
        } else if (!hasValidWidth && 'width' in attrs) {
          errors.push(`${filePath}: <${tag}> has invalid width attribute value ("${attrs['width']}"). Must be a positive integer.`);
        } else if (!hasValidHeight && 'height' in attrs) {
          errors.push(`${filePath}: <${tag}> has invalid height attribute value ("${attrs['height']}"). Must be a positive integer.`);
        } else {
          errors.push(`${filePath}: <${tag}> tag lacks complete dimensions (requires BOTH width and height attributes, valid CSS width/height, or a valid CSS aspect-ratio property to prevent CLS layout shift).`);
        }
      }
    }

  // 2. Blocking synchronous <script> tags in <head>
  const headNodes = findElements(doc, 'head');
  if (headNodes.length > 0) {
    const scriptNodes = findElements(headNodes[0], 'script');
    for (const sNode of scriptNodes) {
      const sAttrs = {};
      for (const a of (sNode.attrs || [])) {
        sAttrs[a.name.toLowerCase()] = a.value;
      }
      const isAsync = 'async' in sAttrs;
      const isDefer = 'defer' in sAttrs;
      const isModule = sAttrs['type'] === 'module';
      const isInline = !('src' in sAttrs);
      if (!isInline && !isAsync && !isDefer && !isModule) {
        errors.push(`${filePath}: Synchronous blocking <script> in <head> without defer/async.`);
      }
    }
  }

  // 3. DOM nesting depth limit (< 32 levels) using parse5 AST
  const maxDepth = calculateMaxDomDepth(content, filePath);
  if (maxDepth > 32) {
    errors.push(`${filePath}: Excessive DOM depth of ${maxDepth} levels (Budget max is 32).`);
  }
}

if (isMain) {
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
}
