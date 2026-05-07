// Locate the cflt-ai repo root and validate the layout we depend on.
// In dev, the repo root is the parent of `app/`. In a packaged build, this
// will be configurable via user settings. Phase A: dev-only, parent dir.

import { existsSync, statSync } from 'node:fs';
import { dirname, join, normalize, relative, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const REQUIRED = ['wiki', 'outputs', 'tools', 'canon', '.claude'];

let cachedRoot: string | null = null;

export function getRepoRoot(): string {
  if (cachedRoot) return cachedRoot;

  // app/out/main/index.js or app/src/main/index.ts → repo root is two up from app/
  const here = dirname(fileURLToPath(import.meta.url));
  // Walk up until we find a dir with all the REQUIRED children.
  let cur = here;
  for (let i = 0; i < 8; i++) {
    if (REQUIRED.every((d) => existsSync(join(cur, d)))) {
      cachedRoot = cur;
      return cur;
    }
    const parent = dirname(cur);
    if (parent === cur) break;
    cur = parent;
  }
  throw new Error(
    `cflt-ai repo root not found from ${here}. Expected dirs: ${REQUIRED.join(', ')}`,
  );
}

/**
 * Resolve a repo-relative path to absolute, with a path-traversal guard.
 * Throws if the resolved path escapes the repo root.
 */
export function resolveInRepo(relPath: string): string {
  const root = getRepoRoot();
  const abs = resolve(root, normalize(relPath));
  const rel = relative(root, abs);
  if (rel.startsWith('..') || resolve(root, rel) !== abs) {
    throw new Error(`Path traversal blocked: ${relPath}`);
  }
  return abs;
}

export function pathExists(relPath: string): boolean {
  try {
    return existsSync(resolveInRepo(relPath));
  } catch {
    return false;
  }
}

export function isDir(relPath: string): boolean {
  try {
    const abs = resolveInRepo(relPath);
    return existsSync(abs) && statSync(abs).isDirectory();
  } catch {
    return false;
  }
}
