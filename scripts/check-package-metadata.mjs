#!/usr/bin/env node
import fs from 'node:fs';

const pkg = JSON.parse(fs.readFileSync(new URL('../package.json', import.meta.url), 'utf8'));
const lock = JSON.parse(fs.readFileSync(new URL('../package-lock.json', import.meta.url), 'utf8'));

const rootPkg = lock.packages?.[''] || {};
const mismatches = [];

if (lock.name !== pkg.name) mismatches.push(`lockfile root name "${lock.name}" != package.json name "${pkg.name}"`);
if (rootPkg.name !== pkg.name) mismatches.push(`lockfile packages[""].name "${rootPkg.name}" != package.json name "${pkg.name}"`);
if (lock.version !== pkg.version) mismatches.push(`lockfile version "${lock.version}" != package.json version "${pkg.version}"`);
if (rootPkg.version !== pkg.version) mismatches.push(`lockfile packages[""].version "${rootPkg.version}" != package.json version "${pkg.version}"`);

if (mismatches.length > 0) {
  console.error('Package metadata mismatch detected:\n- ' + mismatches.join('\n- '));
  process.exit(1);
}

console.log(`Package metadata is consistent for ${pkg.name}@${pkg.version}.`);
