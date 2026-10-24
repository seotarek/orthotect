/**
 * Orthotect Configuration Loader (Node.js/ESM)
 * Zero-dependency JSON config resolver matching core/config.py.
 */
import fs from 'fs';
import path from 'path';

export const DEFAULT_CONFIG = {
  version: '1.0',
  exclude: [
    '**/node_modules/**',
    '**/.git/**',
    '**/dist/**',
    '**/build/**',
    '**/__pycache__/**',
    '**/.gemini/**',
    '**/.claude/**',
    '**/tmp/**'
  ],
  bidi: {
    allowCamelCase: false
  },
  cwv: {
    maxDomDepth: 32,
    maxDomNodes: 1500
  },
  contrast: {
    level: 'AA'
  }
};

const CONFIG_FILENAME = 'orthotect.config.json';

export function findConfigFile(startPath) {
  let current = startPath ? path.resolve(startPath) : process.cwd();
  if (fs.existsSync(current) && fs.statSync(current).isFile()) {
    current = path.dirname(current);
  }

  while (true) {
    const candidate = path.join(current, CONFIG_FILENAME);
    if (fs.existsSync(candidate) && fs.statSync(candidate).isFile()) {
      return candidate;
    }
    const parent = path.dirname(current);
    if (parent === current) break;
    current = parent;
  }
  return null;
}

function deepMerge(base, override) {
  const result = { ...base };
  for (const [key, value] of Object.entries(override)) {
    if (key === '__proto__' || key === 'constructor' || key === 'prototype') continue;
    if (result[key] && typeof result[key] === 'object' && !Array.isArray(result[key]) &&
        value && typeof value === 'object' && !Array.isArray(value)) {
      result[key] = deepMerge(result[key], value);
    } else {
      result[key] = value;
    }
  }
  return result;
}

export function loadOrthotectConfig(projectPath) {
  const configFile = findConfigFile(projectPath);
  if (!configFile) {
    return { config: JSON.parse(JSON.stringify(DEFAULT_CONFIG)), configFile: null };
  }

  try {
    const raw = fs.readFileSync(configFile, 'utf-8');
    const userConfig = JSON.parse(raw);
    const merged = deepMerge(DEFAULT_CONFIG, userConfig);
    return { config: merged, configFile };
  } catch (err) {
    console.warn(`⚠️ [Orthotect Config] Warning: Failed to parse ${configFile}: ${err.message}`);
    return { config: JSON.parse(JSON.stringify(DEFAULT_CONFIG)), configFile: null };
  }
}
