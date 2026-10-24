#!/usr/bin/env node
/**
 * Orthotect Skills Specification Validator
 * Validates all installed skills against the Agent Skills Specification:
 * - Proper YAML frontmatter boundaries (---)
 * - Name: lowercase alphanumeric, hyphens, 1-64 chars, no consecutive hyphens, matches directory
 * - Description: 1-1024 chars, actionable trigger phrases, scope boundaries
 * - Progressive disclosure: SKILL.md under 500 lines (depth moved to references/)
 * - Reference integrity: no orphan files in references/, no dead relative links
 * - License: valid standard license
 *
 * Adapted from Marketingskills specification validator under MIT License (Copyright 2025 Corey Haines).
 */

import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, '..');
const SKILLS_DIR = process.env.SKILLS_DIR ? path.resolve(ROOT, process.env.SKILLS_DIR) : path.join(ROOT, 'skills');

export function extractHeadingSlugs(markdownText) {
  const slugs = new Set();
  const headingLines = markdownText.match(/^#{1,6}\s+(.+)$/gm) || [];
  for (const h of headingLines) {
    const rawTitle = h.replace(/^#{1,6}\s+/, '').trim();
    // GitHub-style anchor slug: lowercase, strip punctuation, spaces to dashes
    const slug = rawTitle
      .toLowerCase()
      .replace(/[^\w\s-]/g, '')
      .trim()
      .replace(/\s+/g, '-');
    slugs.add(slug);
    // Also include pure alphanumeric hyphen slug
    slugs.add(rawTitle.toLowerCase().replace(/[^a-z0-9\s-]/g, '').trim().replace(/\s+/g, '-'));
  }
  return slugs;
}

export function validateSkills(skillsDirectory = SKILLS_DIR) {
  const results = {
    total: 0,
    passed: 0,
    warnings: 0,
    errors: 0,
    details: []
  };

  const rootLicense = path.join(ROOT, 'LICENSE');
  if (!fs.existsSync(rootLicense)) {
    results.errors++;
    results.details.push({
      name: 'repository-root',
      file: rootLicense,
      errors: ['Missing required LICENSE file at repository root'],
      warnings: []
    });
  }

  if (!fs.existsSync(skillsDirectory)) {
    throw new Error(`Skills directory not found: ${skillsDirectory}`);
  }

  const entries = fs.readdirSync(skillsDirectory, { withFileTypes: true });
  const skillDirs = entries.filter(e => e.isDirectory() && !e.name.startsWith('.'));

  for (const dir of skillDirs) {
    const skillName = dir.name;
    const skillPath = path.join(skillsDirectory, skillName);
    const skillFile = path.join(skillPath, 'SKILL.md');

    results.total++;
    const skillReport = {
      name: skillName,
      file: skillFile,
      errors: [],
      warnings: []
    };

    if (!fs.existsSync(skillFile)) {
      skillReport.errors.push(`Missing SKILL.md in skills/${skillName}`);
      results.errors++;
      results.details.push(skillReport);
      continue;
    }

    const content = fs.readFileSync(skillFile, 'utf8').replace(/\r\n/g, '\n');
    const lines = content.split('\n');

    // 1. Frontmatter Boundary Check
    if (!content.startsWith('---\n')) {
      skillReport.errors.push("Missing opening frontmatter delimiter '---'");
    }
    const endFmIndex = content.indexOf('\n---\n', 4);
    if (endFmIndex === -1 && !content.slice(4).startsWith('---\n')) {
      skillReport.errors.push("Missing closing frontmatter delimiter '---'");
    }

    const frontmatter = (endFmIndex !== -1) ? content.substring(4, endFmIndex) : '';

    // 2. Name Validation
    const nameMatch = frontmatter.match(/^name:\s*(.+)$/m);
    if (!nameMatch) {
      skillReport.errors.push("Missing 'name:' in frontmatter");
    } else {
      const declaredName = nameMatch[1].trim().replace(/^['"]|['"]$/g, '');
      if (declaredName !== skillName) {
        skillReport.errors.push(`Name mismatch: directory '${skillName}' != frontmatter '${declaredName}'`);
      }
      if (!/^[a-z0-9]([a-z0-9-]{0,62}[a-z0-9])?$/.test(declaredName)) {
        skillReport.errors.push(`Invalid name format: '${declaredName}' (must be lowercase alphanumeric + hyphens, 1-64 chars)`);
      }
      if (declaredName.includes('--')) {
        skillReport.errors.push(`Name contains consecutive hyphens: '${declaredName}'`);
      }
    }

    // 3. Description Validation
    const descMatch = frontmatter.match(/^description:\s*(.+)$/m);
    if (!descMatch) {
      skillReport.errors.push("Missing 'description:' in frontmatter");
    } else {
      let desc = descMatch[1].trim();
      if ((desc.startsWith('"') && desc.endsWith('"')) || (desc.startsWith("'") && desc.endsWith("'"))) {
        desc = desc.slice(1, -1);
      }
      if (desc.length < 10) {
        skillReport.errors.push(`Description too short (${desc.length} chars)`);
      }
      if (desc.length > 1024) {
        skillReport.errors.push(`Description exceeds 1024 characters (${desc.length} chars)`);
      }
      if (!/(when|use|enforce|audit|generate|master|optimize|verify)/i.test(desc)) {
        skillReport.warnings.push("Description lacks clear action/trigger words ('when', 'use', 'enforce', etc.)");
      }
    }

    // License Validation (if declared in frontmatter)
    const licenseMatch = frontmatter.match(/^license:\s*(.+)$/m);
    if (licenseMatch) {
      const declaredLicense = licenseMatch[1].trim().replace(/^['"]|['"]$/g, '');
      const validSpdx = new Set(['MIT', 'Apache-2.0', 'BSD-2-Clause', 'BSD-3-Clause', 'ISC', 'GPL-3.0', 'LGPL-3.0', 'MPL-2.0', 'Unlicense', 'CC0-1.0']);
      if (!validSpdx.has(declaredLicense)) {
        skillReport.errors.push(`Invalid license SPDX identifier '${declaredLicense}' in frontmatter`);
      }
    }

    // 4. File Length & Progressive Disclosure
    if (lines.length > 1000) {
      skillReport.errors.push(`SKILL.md is ${lines.length} lines (>1000 lines); progressive disclosure requires moving deep specifications to references/`);
    } else if (lines.length > 500) {
      skillReport.warnings.push(`SKILL.md is ${lines.length} lines (>500 lines); consider moving deep specs to references/`);
    }

    // 5. Reference File Integrity
    const refsDir = path.join(skillPath, 'references');
    if (fs.existsSync(refsDir) && fs.statSync(refsDir).isDirectory()) {
      const refFiles = fs.readdirSync(refsDir).filter(f => f.endsWith('.md'));
      for (const rf of refFiles) {
        // Every reference file must be linked from SKILL.md or a sibling reference
        const refRelative = `references/${rf}`;
        const isLinkedFromSkill = content.includes(refRelative) || content.includes(rf);
        let isLinkedFromSibling = false;

        for (const sibling of refFiles) {
          if (sibling !== rf) {
            const sibContent = fs.readFileSync(path.join(refsDir, sibling), 'utf8');
            if (sibContent.includes(rf) || sibContent.includes(refRelative)) {
              isLinkedFromSibling = true;
              break;
            }
          }
        }

        if (!isLinkedFromSkill && !isLinkedFromSibling) {
          skillReport.warnings.push(`Orphan reference file: 'references/${rf}' is not linked from SKILL.md or siblings`);
        }
      }
    }

    // 6. Dead Relative Link and Anchor Verification (SKILL.md and references/*.md)
    const checkLinks = (fileContent, baseDir, sourceFileDesc) => {
      const linkMatches = fileContent.matchAll(/\[([^\]]+)\]\(([^)]+)\)/g);
      for (const match of linkMatches) {
        let href = match[2].trim();
        if (href.includes(' "')) {
          href = href.split(' "')[0].trim();
        }
        if (href.startsWith('http://') || href.startsWith('https://') || href.startsWith('mailto:')) {
          continue;
        }

        if (href.startsWith('#')) {
          const anchor = href.slice(1).toLowerCase();
          const slugs = extractHeadingSlugs(fileContent);
          if (!slugs.has(anchor)) {
            skillReport.errors.push(`Broken anchor link in ${sourceFileDesc}: '${href}' (heading '#${anchor}' not found)`);
          }
          continue;
        }

        if (href.includes('#')) {
          const [filePart, anchorPart] = href.split('#');
          const targetPath = path.resolve(baseDir, filePart);
          if (!fs.existsSync(targetPath)) {
            skillReport.errors.push(`Dead relative link in ${sourceFileDesc}: '${filePart}' does not resolve to an existing file`);
          } else if (targetPath.endsWith('.md')) {
            const targetContent = fs.readFileSync(targetPath, 'utf8');
            const slugs = extractHeadingSlugs(targetContent);
            const anchor = anchorPart.toLowerCase();
            if (!slugs.has(anchor)) {
              skillReport.errors.push(`Broken anchor in ${sourceFileDesc}: '${href}' (heading '#${anchor}' not found in '${filePart}')`);
            }
          }
          continue;
        }

        const targetPath = path.resolve(baseDir, href);
        if (!fs.existsSync(targetPath)) {
          skillReport.errors.push(`Dead relative link in ${sourceFileDesc}: '${href}' does not resolve to an existing file`);
        }
      }
    };

    checkLinks(content, skillPath, 'SKILL.md');

    if (fs.existsSync(refsDir) && fs.statSync(refsDir).isDirectory()) {
      const refFiles = fs.readdirSync(refsDir).filter(f => f.endsWith('.md'));
      for (const rf of refFiles) {
        const rfPath = path.join(refsDir, rf);
        const rfContent = fs.readFileSync(rfPath, 'utf8');
        checkLinks(rfContent, refsDir, `references/${rf}`);
      }
    }

    if (skillReport.errors.length > 0) {
      results.errors++;
    } else if (skillReport.warnings.length > 0) {
      results.warnings++;
      results.passed++;
    } else {
      results.passed++;
    }

    results.details.push(skillReport);
  }

  return results;
}

// CLI Execution
if (process.argv[1] && process.argv[1].endsWith('validate-skills.mjs')) {
  console.log("🔍 Validating Orthotect Skills Against Agent Skills Specification...\n");
  try {
    const res = validateSkills();
    for (const r of res.details) {
      if (r.errors.length > 0) {
        console.error(`❌ ${r.name}`);
        for (const err of r.errors) console.error(`   Error: ${err}`);
        for (const warn of r.warnings) console.warn(`   Warning: ${warn}`);
      } else if (r.warnings.length > 0) {
        console.warn(`⚠️  ${r.name}`);
        for (const warn of r.warnings) console.warn(`   Warning: ${warn}`);
      } else {
        console.log(`✅ ${r.name}`);
      }
    }

    console.log(`\n======================================================`);
    console.log(`Summary: ${res.passed} passed, ${res.warnings} warnings, ${res.errors} errors (${res.total} total skills)`);

    if (res.errors > 0) {
      process.exit(1);
    }
  } catch (err) {
    console.error("Validation failed with exception:", err.message);
    process.exit(1);
  }
}
