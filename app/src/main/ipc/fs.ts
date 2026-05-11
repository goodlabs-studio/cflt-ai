// Filesystem IPC handlers. Read-only surface over the cflt-ai repo.
// Path-traversal guard runs on every IPC entry via resolveInRepo().

import { existsSync, readdirSync, readFileSync, statSync } from 'node:fs';
import { basename, extname, join, relative } from 'node:path';
import { ipcMain, type WebContents } from 'electron';
import chokidar, { type FSWatcher } from 'chokidar';
import matter from 'gray-matter';
import {
  getRepoRoot,
  resolveInRepo,
  pathExists,
  isDir,
} from '../repo.js';
import type {
  ActivityEntry,
  FsEvent,
  GraphEdge,
  IncidentMeta,
  PlanDoc,
  PlanMeta,
  QueueSection,
  ReportMeta,
  WikiArticle,
  WikiNode,
} from '@shared/types';

// ─── tree / article reads ──────────────────────────────────────────────

const WIKI_SECTIONS = ['concepts', 'patterns', 'synthesis'] as const;

function listMarkdownFiles(absDir: string, repoRoot: string): WikiNode[] {
  if (!existsSync(absDir)) return [];
  return readdirSync(absDir)
    .filter((f) => f.endsWith('.md') && !f.startsWith('_'))
    .sort()
    .map<WikiNode>((f) => ({
      name: f.replace(/\.md$/, ''),
      path: relative(repoRoot, join(absDir, f)),
      type: 'article',
    }));
}

function listWikiTree(): WikiNode[] {
  const root = getRepoRoot();
  return WIKI_SECTIONS.map((section) => ({
    name: section,
    path: `wiki/${section}`,
    type: 'section' as const,
    children: listMarkdownFiles(join(root, 'wiki', section), root),
  }));
}

// gray-matter parses YAML dates (e.g. `last_updated: 2026-05-01`) into
// JS Date objects. IPC serializes them as { } losing the value, and the
// renderer crashes when something tries to render them as React children.
// Coerce all Date values to ISO strings before crossing the wire.
function coerceDates(value: unknown): unknown {
  if (value instanceof Date) return value.toISOString().slice(0, 10);
  if (Array.isArray(value)) return value.map(coerceDates);
  if (value && typeof value === 'object') {
    const out: Record<string, unknown> = {};
    for (const [k, v] of Object.entries(value as Record<string, unknown>)) {
      out[k] = coerceDates(v);
    }
    return out;
  }
  return value;
}

function readWiki(repoRelPath: string): WikiArticle {
  const abs = resolveInRepo(repoRelPath);
  const raw = readFileSync(abs, 'utf-8');
  const { data, content } = matter(raw);
  return {
    path: repoRelPath,
    frontmatter: coerceDates(data) as WikiArticle['frontmatter'],
    body: content,
  };
}

// ─── graph (wiki/_graph.md) ────────────────────────────────────────────

const GRAPH_LINE = /^(\S+)\s+→\s+(\S+)\s*:\s*(.+)$/;

function readGraph(): GraphEdge[] {
  const path = 'wiki/_graph.md';
  if (!pathExists(path)) return [];
  const raw = readFileSync(resolveInRepo(path), 'utf-8');
  const edges: GraphEdge[] = [];
  for (const line of raw.split('\n')) {
    const m = GRAPH_LINE.exec(line.trim());
    if (m) edges.push({ source: m[1], target: m[2], relationship: m[3] });
  }
  return edges;
}

// ─── queue (wiki/_queue.md) ────────────────────────────────────────────

function readQueue(): QueueSection[] {
  const path = 'wiki/_queue.md';
  if (!pathExists(path)) return [];
  const raw = readFileSync(resolveInRepo(path), 'utf-8');
  const sections: QueueSection[] = [];
  let current: QueueSection | null = null;
  for (const line of raw.split('\n')) {
    const headingMatch = /^##\s+(.+)$/.exec(line);
    if (headingMatch) {
      if (current) sections.push(current);
      current = { heading: headingMatch[1].trim(), entries: [] };
      continue;
    }
    if (current && line.trim()) current.entries.push(line);
  }
  if (current) sections.push(current);
  return sections;
}

// ─── activity (wiki/activity/YYYY-MM.md) ───────────────────────────────

function listActivityMonths(): string[] {
  const dir = 'wiki/activity';
  if (!pathExists(dir)) return [];
  return readdirSync(resolveInRepo(dir))
    .filter((f) => /^\d{4}-\d{2}\.md$/.test(f))
    .map((f) => f.replace(/\.md$/, ''))
    .sort();
}

function readActivity(month?: string): ActivityEntry[] {
  const months = month ? [month] : listActivityMonths();
  const entries: ActivityEntry[] = [];
  for (const m of months) {
    const path = `wiki/activity/${m}.md`;
    if (!pathExists(path)) continue;
    const raw = readFileSync(resolveInRepo(path), 'utf-8');
    // Split on H2 headings; first chunk is preamble (skip).
    const chunks = raw.split(/^##\s+/m).slice(1);
    for (const chunk of chunks) {
      const firstLineEnd = chunk.indexOf('\n');
      const timestamp = chunk.slice(0, firstLineEnd).trim();
      const body = chunk.slice(firstLineEnd + 1);
      entries.push({
        timestamp,
        skill: extractField(body, 'Skill') || 'unknown',
        overlay: extractField(body, 'Overlay'),
        input: extractField(body, 'Input'),
        output: extractField(body, 'Output'),
        canonStack: extractField(body, 'Canon stack'),
        raw: `## ${timestamp}\n${body}`,
      });
    }
  }
  // Newest first
  return entries.sort((a, b) => b.timestamp.localeCompare(a.timestamp));
}

function extractField(body: string, name: string): string | undefined {
  const re = new RegExp(`^\\*\\*${name}:\\*\\*\\s*(.+)$`, 'm');
  const m = re.exec(body);
  return m ? m[1].trim() : undefined;
}

// ─── incidents ─────────────────────────────────────────────────────────

function listIncidents(): IncidentMeta[] {
  const dir = 'wiki/incidents';
  if (!isDir(dir)) return []; // lazily created by apply_engine.write_incident_article()
  return readdirSync(resolveInRepo(dir))
    .filter((f) => f.endsWith('.md'))
    .sort()
    .map((f) => {
      const repoPath = `${dir}/${f}`;
      const raw = readFileSync(resolveInRepo(repoPath), 'utf-8');
      const { data } = matter(raw);
      return {
        path: repoPath,
        title: typeof data['title'] === 'string' ? data['title'] : f.replace(/\.md$/, ''),
        date: typeof data['date'] === 'string' ? data['date'] : undefined,
      };
    });
}

// ─── reports ───────────────────────────────────────────────────────────

const REPORT_FOOTER_RE =
  /\*Validated against [^.]+\.\s*(\d+)\s*claims? checked,\s*(\d+)\s*corrected,\s*(\d+)\s*unverifiable\.?\*/i;

function listReports(): ReportMeta[] {
  const dir = 'outputs/reports';
  if (!isDir(dir)) return [];
  return readdirSync(resolveInRepo(dir))
    .filter((f) => f.endsWith('.md'))
    .sort()
    .reverse()
    .map<ReportMeta>((f) => {
      const slug = f.replace(/\.md$/, '');
      const repoPath = `${dir}/${f}`;
      const raw = readFileSync(resolveInRepo(repoPath), 'utf-8');
      const dateMatch = /(\d{4}-\d{2}-\d{2})/.exec(slug);
      const skillMatch = /^.*Skill:\*\*\s*(\S+)/m.exec(raw);
      const footerMatch = REPORT_FOOTER_RE.exec(raw);
      return {
        slug,
        path: repoPath,
        date: dateMatch?.[1],
        sourceSkill: skillMatch?.[1],
        claimsChecked: footerMatch ? Number(footerMatch[1]) : undefined,
        claimsCorrected: footerMatch ? Number(footerMatch[2]) : undefined,
        claimsUnverifiable: footerMatch ? Number(footerMatch[3]) : undefined,
      };
    });
}

function readReport(slug: string): string {
  const repoPath = `outputs/reports/${slug}.md`;
  return readFileSync(resolveInRepo(repoPath), 'utf-8');
}

// ─── plans ─────────────────────────────────────────────────────────────

function listPlans(): PlanMeta[] {
  const dir = 'outputs/plans';
  if (!isDir(dir)) return [];
  return readdirSync(resolveInRepo(dir))
    .filter((f) => f.endsWith('.md'))
    .sort()
    .reverse()
    .map<PlanMeta>((f) => {
      const slug = f.replace(/\.md$/, '');
      const repoPath = `${dir}/${f}`;
      const dateMatch = /(\d{4}-\d{2}-\d{2})/.exec(slug);
      return { slug, path: repoPath, date: dateMatch?.[1] };
    });
}

function readPlan(repoPath: string): PlanDoc {
  const raw = readFileSync(resolveInRepo(repoPath), 'utf-8');
  const slug = basename(repoPath, extname(repoPath));
  const dateMatch = /(\d{4}-\d{2}-\d{2})/.exec(slug);
  const artifactMatch = /Artifact:\s*`([^`]+)`/.exec(raw);
  return {
    meta: {
      slug,
      path: repoPath,
      date: dateMatch?.[1],
      artifact: artifactMatch?.[1],
    },
    body: raw,
  };
}

// ─── overlays / canon ──────────────────────────────────────────────────

function listOverlays(): string[] {
  const dir = 'canon/customer';
  if (!isDir(dir)) return [];
  return readdirSync(resolveInRepo(dir))
    .filter((name) => isDir(`${dir}/${name}`))
    .sort();
}

function activeLayers(): string[] {
  // canon/stack.py is the source of truth, but Phase A keeps this
  // dependency-free. Phase E wires the python shell-out for true active
  // layer resolution from `resolve_stack(...)`.
  const layers = ['base'];
  if (isDir('canon/industry/fsi')) layers.push('industry/fsi');
  return layers;
}

// ─── watch (chokidar bridge) ───────────────────────────────────────────

const watchers = new Map<string, FSWatcher>();

function startWatch(
  webContents: WebContents,
  watchId: string,
  globs: string[],
): void {
  if (watchers.has(watchId)) {
    watchers.get(watchId)!.close().catch(() => {});
  }
  const root = getRepoRoot();
  const absGlobs = globs.map((g) => join(root, g));
  const watcher = chokidar.watch(absGlobs, {
    ignoreInitial: true,
    awaitWriteFinish: { stabilityThreshold: 200, pollInterval: 50 },
  });
  const send = (kind: FsEvent['kind'], abs: string): void => {
    if (webContents.isDestroyed()) return;
    webContents.send('fs:watch:event', watchId, {
      kind,
      path: relative(root, abs),
    });
  };
  watcher.on('add', (p) => send('add', p));
  watcher.on('change', (p) => send('change', p));
  watcher.on('unlink', (p) => send('unlink', p));
  watchers.set(watchId, watcher);
}

function stopWatch(watchId: string): void {
  const w = watchers.get(watchId);
  if (w) {
    w.close().catch(() => {});
    watchers.delete(watchId);
  }
}

// ─── registration ──────────────────────────────────────────────────────

export function registerFsHandlers(): void {
  ipcMain.handle('fs:listWikiTree', async () => listWikiTree());
  ipcMain.handle('fs:readWiki', async (_e, p: string) => readWiki(p));
  ipcMain.handle('fs:readGraph', async () => readGraph());
  ipcMain.handle('fs:readQueue', async () => readQueue());
  ipcMain.handle('fs:readActivity', async (_e, m?: string) => readActivity(m));
  ipcMain.handle('fs:listIncidents', async () => listIncidents());
  ipcMain.handle('fs:listReports', async () => listReports());
  ipcMain.handle('fs:readReport', async (_e, slug: string) => readReport(slug));
  ipcMain.handle('fs:listPlans', async () => listPlans());
  ipcMain.handle('fs:readPlan', async (_e, p: string) => readPlan(p));
  ipcMain.handle('fs:listOverlays', async () => listOverlays());
  ipcMain.handle('fs:activeLayers', async () => activeLayers());

  ipcMain.on('fs:watch:start', (e, watchId: string, globs: string[]) => {
    startWatch(e.sender, watchId, globs);
  });
  ipcMain.on('fs:watch:stop', (_e, watchId: string) => {
    stopWatch(watchId);
  });

  ipcMain.handle('meta:repoRoot', async () => getRepoRoot());
  ipcMain.handle('meta:appVersion', async () => '0.1.0');
}

export function disposeWatchers(): void {
  for (const w of watchers.values()) w.close().catch(() => {});
  watchers.clear();
}
