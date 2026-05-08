// Python tool IPC. Wraps wiki-lint, wiki-search, wiki-stats, and
// review-to-docx so the renderer can call them as typed functions.

import { resolve as pathResolve } from 'node:path';
import { existsSync } from 'node:fs';
import { ipcMain } from 'electron';
import {
  collectTool,
  streamTool,
  cancelTool,
  disposeAllTools,
} from '../claude/tool-runner.js';
import { getRepoRoot, resolveInRepo } from '../repo.js';
import type { SearchHit, WikiStats, WikiStatsBucket } from '@shared/types';

// ─── parsers for python tool stdout ────────────────────────────────────

const SEARCH_HEADER_RE = /^\[\s*(\d+)\s*\]\s+(\S.*?)\s*$/;

export function parseSearchOutput(stdout: string): SearchHit[] {
  const lines = stdout.split('\n');
  const hits: SearchHit[] = [];
  for (let i = 0; i < lines.length; i++) {
    const m = SEARCH_HEADER_RE.exec(lines[i]);
    if (!m) continue;
    const score = Number(m[1]);
    const path = m[2];
    let preview = '';
    // Next non-blank line is the preview (title or first match).
    for (let j = i + 1; j < lines.length; j++) {
      const trimmed = lines[j].trim();
      if (trimmed) {
        preview = trimmed.replace(/^title:\s*/, '');
        break;
      }
    }
    hits.push({ path, score, preview });
  }
  return hits;
}

const STATS_INT_RE = /^\s*(Articles|Total words|Raw sources):\s*([\d,]+)/;
const STATS_BUCKET_RE = /^\s{4,}(\S(?:.*?\S)?)\s+(\d+)\s*$/;

export function parseStatsOutput(stdout: string): WikiStats {
  const lines = stdout.split('\n');
  let articles = 0;
  let totalWords = 0;
  let rawSources = 0;
  const bySection: WikiStatsBucket[] = [];
  const byConfidence: WikiStatsBucket[] = [];
  const topTags: WikiStatsBucket[] = [];
  let section: 'section' | 'confidence' | 'tags' | null = null;

  for (const raw of lines) {
    const intMatch = STATS_INT_RE.exec(raw);
    if (intMatch) {
      const value = Number(intMatch[2].replace(/,/g, ''));
      if (intMatch[1] === 'Articles') articles = value;
      else if (intMatch[1] === 'Total words') totalWords = value;
      else if (intMatch[1] === 'Raw sources') rawSources = value;
      continue;
    }
    if (/^\s*By section:/.test(raw)) {
      section = 'section';
      continue;
    }
    if (/^\s*By confidence:/.test(raw)) {
      section = 'confidence';
      continue;
    }
    if (/^\s*Top tags:/.test(raw)) {
      section = 'tags';
      continue;
    }
    const bucketMatch = STATS_BUCKET_RE.exec(raw);
    if (bucketMatch && section) {
      const bucket: WikiStatsBucket = {
        name: bucketMatch[1].trim(),
        count: Number(bucketMatch[2]),
      };
      if (section === 'section') bySection.push(bucket);
      else if (section === 'confidence') byConfidence.push(bucket);
      else if (section === 'tags') topTags.push(bucket);
    }
  }

  return { articles, totalWords, rawSources, bySection, byConfidence, topTags };
}

// ─── IPC registration ──────────────────────────────────────────────────

export function registerToolHandlers(): void {
  ipcMain.handle(
    'tool:wikiLint:start',
    async (e, args?: { full?: boolean; fix?: boolean }) => {
      const flags: string[] = [];
      if (args?.full) flags.push('--full');
      if (args?.fix) flags.push('--fix');
      return streamTool(e.sender, 'wiki-lint.py', flags);
    },
  );
  ipcMain.handle('tool:wikiLint:cancel', async (_e, toolId: string) =>
    cancelTool(toolId),
  );

  ipcMain.handle('tool:wikiSearch', async (_e, query: string) => {
    const { stdout } = await collectTool('wiki-search.py', [query]);
    return parseSearchOutput(stdout);
  });

  ipcMain.handle('tool:wikiStats', async () => {
    const { stdout } = await collectTool('wiki-stats.py');
    return parseStatsOutput(stdout);
  });

  ipcMain.handle('tool:reviewToDocx', async (_e, reportPath: string) => {
    // Validate the report path is in-repo before passing to subprocess
    let absInput: string;
    try {
      absInput = resolveInRepo(reportPath);
    } catch (err) {
      throw new Error(`invalid report path: ${(err as Error).message}`);
    }
    if (!existsSync(absInput)) {
      throw new Error(`report file not found: ${reportPath}`);
    }
    const { exitCode, stdout, stderr } = await collectTool(
      'review-to-docx.py',
      [reportPath],
    );
    if (exitCode !== 0) {
      throw new Error(
        `review-to-docx exited ${exitCode}: ${stderr.trim().slice(-400)}`,
      );
    }
    // Tool prints the output path on the last non-blank line of stdout.
    const lines = stdout
      .trim()
      .split('\n')
      .map((l) => l.trim())
      .filter(Boolean);
    const last = lines[lines.length - 1] ?? '';
    // Find a path-like fragment ending in .docx
    const m = /([^\s]+\.docx)/.exec(last);
    if (!m) {
      // Fall back: output path is sibling of input with .docx extension
      return pathResolve(getRepoRoot(), reportPath.replace(/\.md$/, '.docx'));
    }
    return pathResolve(getRepoRoot(), m[1]);
  });
}

export { disposeAllTools as disposeToolSubprocesses };
