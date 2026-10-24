#!/usr/bin/env node
/**
 * Orthotect Gate: DOM Structure & Layout-Shift (CLS) Budget
 * Verifies that media elements reserve dimensions and DOM depth stays within bounds.
 */
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

import * as parse5 from 'parse5';
import { loadOrthotectConfig } from '../core/config.mjs';

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

  // Single length/percentage dimension check: e.g. "200px", "0.5px", ".5em", "50%", "10rem", "10ex"
  // Strictly validates positive numeric value (> 0) supporting decimals below 1 and leading decimal dots per W3C CSS Values 4
  const directMatch = clean.match(/^((?:[0-9]+(?:\.[0-9]+)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?)(px|rem|em|vw|vh|%|cqi|cqw|pt|cm|mm|in|vmin|vmax|ch|ex)$/i);
  if (directMatch) {
    const num = parseFloat(directMatch[1]);
    if (!isNaN(num) && num > 0) return true;
    return false;
  }

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

export function calculateSelectorSpecificity(selectorStr) {
  let a = 0, b = 0, c = 0;
  if (!selectorStr || typeof selectorStr !== 'string') return [0, 0, 0];
  const normalized = selectorStr.replace(/\s*>\s*/g, ' > ').trim();
  const compounds = normalized.split(/\s+/).filter(t => t !== '>');
  for (const comp of compounds) {
    if (comp === '*' || !comp) continue;
    const ids = comp.match(/#[a-zA-Z0-9_-]+/g);
    if (ids) a += ids.length;
    const classes = comp.match(/\.[a-zA-Z0-9_-]+/g);
    if (classes) b += classes.length;
    const attrs = comp.match(/\[[^\]]+\]/g);
    if (attrs) b += attrs.length;
    const tagMatch = comp.match(/^([a-zA-Z0-9_-]+)/);
    if (tagMatch && tagMatch[1] !== '*') {
      c += 1;
    }
  }
  return [a, b, c];
}

export function compareSpecificity(specA, specB) {
  if (specA[0] !== specB[0]) return specA[0] - specB[0];
  if (specA[1] !== specB[1]) return specA[1] - specB[1];
  return specA[2] - specB[2];
}

export function parseCssOrderedRules(cssText) {
  const rules = [];
  if (!cssText) return rules;
  const stripped = cssText.replace(/\/\*[\s\S]*?\*\//g, '');
  const ruleRegex = /([^{}]+)\{([^{}]+)\}/g;
  let match;
  let order = 0;
  while ((match = ruleRegex.exec(stripped)) !== null) {
    const selectors = match[1].split(',').map(s => s.trim().toLowerCase()).filter(Boolean);
    const decls = parseStyleDeclarations(match[2]);
    for (const sel of selectors) {
      rules.push({
        selector: sel,
        decls,
        specificity: calculateSelectorSpecificity(sel),
        order: order++
      });
    }
  }
  return rules;
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
  const orderedCssRules = parseCssOrderedRules(combinedCss);

  // 1. Strict media dimension check on parsed AST:
  // Inspects <img>, <video>, and <iframe> elements to prevent CLS layout shift.
  // Resolves full CSS cascade: HTML presentation attributes -> stylesheet rules (specificity + source order) -> inline styles.
  const mediaElements = findElementsWithAncestors(doc, ['img', 'video', 'iframe']);
  for (const { node: el, ancestors } of mediaElements) {
    const tag = el.nodeName.toLowerCase();
    const attrs = {};
    for (const a of (el.attrs || [])) {
      attrs[a.name.toLowerCase()] = a.value;
    }

    // Base presentation attributes
    let cascadedWidth = Object.prototype.hasOwnProperty.call(attrs, 'width') ? { val: attrs['width'], isHtmlAttr: true, isImportant: false } : null;
    let cascadedHeight = Object.prototype.hasOwnProperty.call(attrs, 'height') ? { val: attrs['height'], isHtmlAttr: true, isImportant: false } : null;
    let cascadedAspect = null;

    // Matching CSS stylesheet rules sorted by specificity ascending, then source order ascending
    const matchingRules = [];
    for (const rule of orderedCssRules) {
      if (matchesSelectorChain(el, ancestors, rule.selector)) {
        matchingRules.push(rule);
      }
    }
    matchingRules.sort((r1, r2) => {
      const cmp = compareSpecificity(r1.specificity, r2.specificity);
      if (cmp !== 0) return cmp;
      return r1.order - r2.order;
    });

    for (const rule of matchingRules) {
      if (rule.decls['width']) {
        const isImp = /!important\s*$/i.test(rule.decls['width']);
        if (!cascadedWidth || !cascadedWidth.isImportant || isImp) {
          cascadedWidth = { val: rule.decls['width'], isHtmlAttr: false, isImportant: isImp };
        }
      }
      if (rule.decls['height']) {
        const isImp = /!important\s*$/i.test(rule.decls['height']);
        if (!cascadedHeight || !cascadedHeight.isImportant || isImp) {
          cascadedHeight = { val: rule.decls['height'], isHtmlAttr: false, isImportant: isImp };
        }
      }
      if (rule.decls['aspect-ratio']) {
        const isImp = /!important\s*$/i.test(rule.decls['aspect-ratio']);
        if (!cascadedAspect || !cascadedAspect.isImportant || isImp) {
          cascadedAspect = { val: rule.decls['aspect-ratio'], isHtmlAttr: false, isImportant: isImp };
        }
      }
    }

    // Inline style attribute declarations (specificity (1, 0, 0, 0))
    const styleDecls = parseStyleDeclarations(attrs['style'] || '');
    if (Object.prototype.hasOwnProperty.call(styleDecls, 'width')) {
      const isImp = /!important\s*$/i.test(styleDecls['width']);
      if (!cascadedWidth || !cascadedWidth.isImportant || isImp) {
        cascadedWidth = { val: styleDecls['width'], isHtmlAttr: false, isImportant: isImp, isInline: true };
      }
    }
    if (Object.prototype.hasOwnProperty.call(styleDecls, 'height')) {
      const isImp = /!important\s*$/i.test(styleDecls['height']);
      if (!cascadedHeight || !cascadedHeight.isImportant || isImp) {
        cascadedHeight = { val: styleDecls['height'], isHtmlAttr: false, isImportant: isImp, isInline: true };
      }
    }
    if (Object.prototype.hasOwnProperty.call(styleDecls, 'aspect-ratio')) {
      const isImp = /!important\s*$/i.test(styleDecls['aspect-ratio']);
      if (!cascadedAspect || !cascadedAspect.isImportant || isImp) {
        cascadedAspect = { val: styleDecls['aspect-ratio'], isHtmlAttr: false, isImportant: isImp, isInline: true };
      }
    }

    // Now evaluate winning cascaded values
    let hasValidAspect = false;
    if (cascadedAspect) {
      hasValidAspect = isValidAspectRatioValue(cascadedAspect.val);
      if (!hasValidAspect && cascadedAspect.isInline) {
        errors.push(`${filePath}: <${tag}> has invalid CSS aspect-ratio value in style attribute ("${cascadedAspect.val}"). Must be a positive ratio (e.g. "16/9" or "1").`);
      }
    }

    let hasValidWidth = false;
    if (cascadedWidth) {
      hasValidWidth = cascadedWidth.isHtmlAttr ? isPositiveDimension(cascadedWidth.val) : isValidCssDimensionValue(cascadedWidth.val);
    }
    let hasValidHeight = false;
    if (cascadedHeight) {
      hasValidHeight = cascadedHeight.isHtmlAttr ? isPositiveDimension(cascadedHeight.val) : isValidCssDimensionValue(cascadedHeight.val);
    }

    const hasBothDimensions = hasValidWidth && hasValidHeight;

    if (!hasBothDimensions && !hasValidAspect) {
      if (cascadedWidth && cascadedHeight && (cascadedWidth.isInline || cascadedHeight.isInline)) {
        errors.push(`${filePath}: <${tag}> has invalid non-reserving CSS dimensions in style ("width: ${cascadedWidth.val}; height: ${cascadedHeight.val}"). Must be positive dimensions with valid units.`);
      } else if (attrs['data-width'] || attrs['data-height']) {
        errors.push(`${filePath}: <${tag}> uses data-width/data-height instead of native HTML width/height attributes or CSS aspect-ratio.`);
      } else if ('width' in attrs && !hasValidWidth && cascadedWidth && cascadedWidth.isHtmlAttr) {
        errors.push(`${filePath}: <${tag}> has invalid width attribute value ("${attrs['width']}"). Must be a positive integer.`);
      } else if ('height' in attrs && !hasValidHeight && cascadedHeight && cascadedHeight.isHtmlAttr) {
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

  // 3. DOM nesting depth limit using parse5 AST
  const { config: cwvConfig } = loadOrthotectConfig(filePath);
  const maxAllowedDomDepth = cwvConfig?.cwv?.maxDomDepth ?? 32;
  const maxDepth = calculateMaxDomDepth(content, filePath);
  if (maxDepth > maxAllowedDomDepth) {
    errors.push(`${filePath}: Excessive DOM depth of ${maxDepth} levels (Budget max is ${maxAllowedDomDepth}).`);
  }
}

if (isMain) {
  const resolvedTarget = path.resolve(targetDir);
  const targetStat = fs.statSync(targetDir);
  if (targetStat.isFile() && targetDir.endsWith('.html')) {
    checkHtmlFile(targetDir);
  } else {
    const visitedRealDirs = new Set();
    const scan = (dir) => {
      let realDir;
      try {
        realDir = fs.realpathSync(dir);
      } catch (_) {
        return;
      }
      if (visitedRealDirs.has(realDir)) return;
      visitedRealDirs.add(realDir);

      let entries;
      try {
        entries = fs.readdirSync(dir);
      } catch (_) {
        return;
      }

      for (const f of entries) {
        const full = path.join(dir, f);
        try {
          const lstat = fs.lstatSync(full);
          if (lstat.isSymbolicLink()) {
            const realTarget = fs.realpathSync(full);
            // Check if symlink points outside the target tree
            const rel = path.relative(resolvedTarget, realTarget);
            if (rel.startsWith('..') || path.isAbsolute(rel)) {
              // External symlink - do not traverse outside targetDir
              continue;
            }
            const realStat = fs.statSync(realTarget);
            if (realStat.isDirectory()) {
              if (!['node_modules', '.git', 'dist'].includes(f)) scan(full);
            } else if (f.endsWith('.html')) {
              checkHtmlFile(full);
            }
          } else if (lstat.isDirectory()) {
            if (!['node_modules', '.git', 'dist'].includes(f)) scan(full);
          } else if (f.endsWith('.html')) {
            checkHtmlFile(full);
          }
        } catch (_) {}
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
