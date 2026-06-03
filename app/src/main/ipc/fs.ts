// Filesystem IPC handlers. Read-only surface over the cflt-ai repo
// EXCEPT for removeQueueEntry which performs a targeted write to _queue.md.
// Path-traversal guard runs on every IPC entry via resolveInRepo().

import { existsSync, readdirSync, readFileSync, statSync, writeFileSync } from 'node:fs';
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
import { detectAuthMode } from '../auth.js';
import type {
  ActivityEntry,
  FsEvent,
  GraphEdge,
  IncidentMeta,
  ManifestEntry,
  PlanDoc,
  PlanMeta,
  QueueEntry,
  QueueOrigin,
  QueueStatus,
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

// ─── fsi-dsp asset manifest (raw/repos/fsi-dsp/MANIFEST.yaml) ───────────

const MANIFEST_PATH = 'raw/repos/fsi-dsp/MANIFEST.yaml';

function readManifest(): ManifestEntry[] {
  if (!pathExists(MANIFEST_PATH)) return [];
  const raw = readFileSync(resolveInRepo(MANIFEST_PATH), 'utf-8');
  // Reuse gray-matter's bundled YAML engine by wrapping the whole doc in
  // fences — avoids adding a YAML dependency. Safe: MANIFEST.yaml has no bare
  // `---` lines (its dividers are box-drawing comments).
  const { data } = matter(`---\n${raw}\n---\n`);
  const caps = (data as { capabilities?: unknown }).capabilities;
  if (!Array.isArray(caps)) return [];
  return caps
    .filter(
      (c): c is Record<string, unknown> =>
        !!c && typeof c === 'object' && typeof (c as Record<string, unknown>).id === 'string',
    )
    .map((c) => ({
      id: String(c.id),
      type: String(c.type ?? ''),
      name: String(c.name ?? c.id),
      path: String(c.path ?? ''),
      description: String(c.description ?? ''),
    }));
}

// ─── queue (wiki/_queue.md) ────────────────────────────────────────────
//
// J.1 Ledger: status is DERIVED at read-time by cross-referencing each entry
// against the wiki tree. _queue.md is a backlog of intentions, not a state
// machine. The only write-back path is removeQueueEntry() (user-initiated).
//
// Decay constant mirrors tools/wiki-lint.py DECAY_DAYS=90 (after that,
// `confidence: high` is treated as stale even with a recent last_validated
// timestamp). Do not diverge — keep both in sync if either side changes.

const QUEUE_PATH = 'wiki/_queue.md';
const DECAY_DAYS = 90;

const MD_LINK_RE = /\[([^\]]+)\]\(([^)]+\.md)\)/;
const AUTO_STUB_RE = /<!--\s*auto-stub:\s*([^\s-]+)\s*-->/;
const BARE_PATH_RE = /(wiki\/[a-z]+\/[A-Za-z0-9._/-]+\.md)/;
const STUB_MARKER_RE = /⚠️\s*Stub\b/;
const UNVERIFIED_MARKER_RE = /⚠️\s*unverified\b/;

function inferOriginFromHeading(heading: string): QueueOrigin {
  const h = heading.toLowerCase();
  if (h.includes('auto-stub')) return 'auto-stub';
  if (h.includes('unverified') || h.includes('verify') || h.includes('drift')) return 'claim';
  if (h.includes('lint')) return 'lint';
  if (h.includes('candidate')) return 'candidate';
  return 'stub';
}

function extractPathFromLine(line: string): string | undefined {
  const linkMatch = MD_LINK_RE.exec(line);
  if (linkMatch) return linkMatch[2];
  const bareMatch = BARE_PATH_RE.exec(line);
  if (bareMatch) return bareMatch[1];
  return undefined;
}

function extractTitleFromLine(line: string, fallbackPath?: string): string {
  const linkMatch = MD_LINK_RE.exec(line);
  if (linkMatch) return linkMatch[1];
  if (fallbackPath) {
    return basename(fallbackPath, '.md');
  }
  // Strip leading checkbox + bullet, return first non-trivial segment
  return line.replace(/^\s*-\s*\[[ x]\]\s*/, '').replace(/<!--.*?-->/g, '').trim().slice(0, 120);
}

function extractDescriptionFromLine(line: string): string | undefined {
  // Description is everything after " — " (em dash with spaces)
  const idx = line.indexOf(' — ');
  if (idx === -1) return undefined;
  return line.slice(idx + 3).trim();
}

function isCheckedLine(line: string): boolean {
  return /^\s*-\s*\[x\]/i.test(line);
}

function readFrontmatterSafe(absPath: string): { confidence?: string; last_validated?: string } | null {
  try {
    const raw = readFileSync(absPath, 'utf-8');
    const { data } = matter(raw);
    return {
      confidence: typeof data['confidence'] === 'string' ? data['confidence'] : undefined,
      last_validated:
        data['last_validated'] instanceof Date
          ? data['last_validated'].toISOString().slice(0, 10)
          : typeof data['last_validated'] === 'string'
            ? data['last_validated']
            : undefined,
    };
  } catch {
    return null;
  }
}

function daysSince(isoDate?: string): number | undefined {
  if (!isoDate) return undefined;
  const then = Date.parse(isoDate);
  if (Number.isNaN(then)) return undefined;
  const ms = Date.now() - then;
  return Math.max(0, Math.floor(ms / (24 * 60 * 60 * 1000)));
}

interface DerivationContext {
  indexContent: string;
  edges: GraphEdge[];
}

function buildDerivationContext(): DerivationContext {
  const indexPath = 'wiki/_index.md';
  const indexContent = pathExists(indexPath) ? readFileSync(resolveInRepo(indexPath), 'utf-8') : '';
  const edges = readGraph();
  return { indexContent, edges };
}

function hasInboundEdge(path: string, edges: GraphEdge[]): boolean {
  // Edge target shape from _graph.md: "concepts/sla-tiers" — strip "wiki/" prefix + ".md" suffix
  const normalized = path.replace(/^wiki\//, '').replace(/\.md$/, '');
  return edges.some((e) => e.target === normalized);
}

function isInIndex(path: string, indexContent: string): boolean {
  return indexContent.includes(path);
}

function deriveStatus(
  origin: QueueOrigin,
  checked: boolean,
  path: string | undefined,
  ctx: DerivationContext,
): { status: QueueStatus; confidence?: 'high' | 'medium' | 'low'; lastValidated?: string; daysSinceValidated?: number } {
  // Pre-checked entries (user already marked done) → published
  if (checked) {
    return { status: 'published' };
  }

  // Lint findings: no per-entry article — surface as needs-review until lint clears
  if (origin === 'lint') {
    return { status: 'needs-review' };
  }

  // Claim entries: status hinges on whether the ⚠️ unverified marker still
  // exists at the cited path. If the host file is gone or the marker is gone,
  // the claim is resolved → validated (user can Remove).
  if (origin === 'claim') {
    if (!path) return { status: 'needs-review' };
    if (!pathExists(path)) return { status: 'validated' };
    try {
      const body = readFileSync(resolveInRepo(path), 'utf-8');
      if (UNVERIFIED_MARKER_RE.test(body)) return { status: 'needs-review' };
      return { status: 'validated' };
    } catch {
      return { status: 'needs-review' };
    }
  }

  // Stub / auto-stub / candidate: status hinges on whether the target article
  // exists, its confidence, and whether it's been wired into _index/_graph.
  if (!path) return { status: 'new' };
  if (!pathExists(path)) return { status: 'new' };

  const fm = readFrontmatterSafe(resolveInRepo(path));
  if (!fm) return { status: 'drafted' };

  const confidence = (fm.confidence as 'high' | 'medium' | 'low' | undefined) ?? undefined;
  const lastValidated = fm.last_validated;
  const ageDays = daysSince(lastValidated);

  // Check for ⚠️ Stub marker in body
  let hasStubMarker = false;
  try {
    const body = readFileSync(resolveInRepo(path), 'utf-8');
    hasStubMarker = STUB_MARKER_RE.test(body);
  } catch {
    // ignore
  }

  if (hasStubMarker || confidence === 'low') {
    return { status: 'drafted', confidence, lastValidated, daysSinceValidated: ageDays };
  }
  if (confidence === 'medium') {
    return { status: 'drafted', confidence, lastValidated, daysSinceValidated: ageDays };
  }
  if (confidence === 'high') {
    if (ageDays !== undefined && ageDays > DECAY_DAYS) {
      return { status: 'stale', confidence, lastValidated, daysSinceValidated: ageDays };
    }
    if (isInIndex(path, ctx.indexContent) && hasInboundEdge(path, ctx.edges)) {
      return { status: 'published', confidence, lastValidated, daysSinceValidated: ageDays };
    }
    return { status: 'validated', confidence, lastValidated, daysSinceValidated: ageDays };
  }

  // No confidence field: file exists but isn't a wiki article shape
  return { status: 'drafted' };
}

function readQueue(): QueueEntry[] {
  if (!pathExists(QUEUE_PATH)) return [];
  const raw = readFileSync(resolveInRepo(QUEUE_PATH), 'utf-8');
  const ctx = buildDerivationContext();

  const entries: QueueEntry[] = [];
  let currentSection = '';
  let currentOrigin: QueueOrigin = 'stub';
  let lineIdx = 0;

  // Multi-line auto-stub support: an auto-stub spans 2+ lines (the first has
  // the path + auto-stub marker; subsequent indented lines carry metadata).
  // We treat the first checkbox line as the entry and accumulate continuation
  // text into its description until the next entry or blank line.
  let inAutoStubBody: { entry: QueueEntry; description: string[] } | null = null;

  const flushAutoStub = (): void => {
    if (inAutoStubBody) {
      if (inAutoStubBody.description.length > 0) {
        const extra = inAutoStubBody.description.join(' ').trim();
        inAutoStubBody.entry.description = inAutoStubBody.entry.description
          ? `${inAutoStubBody.entry.description} ${extra}`
          : extra;
      }
      entries.push(inAutoStubBody.entry);
      inAutoStubBody = null;
    }
  };

  for (const line of raw.split('\n')) {
    lineIdx += 1;
    const headingMatch = /^##\s+(.+)$/.exec(line);
    if (headingMatch) {
      flushAutoStub();
      currentSection = headingMatch[1].trim();
      currentOrigin = inferOriginFromHeading(currentSection);
      continue;
    }

    // Skip frontmatter, code-fence, and html-comment-only lines outside auto-stub bodies
    if (!currentSection) continue;
    if (line.trim().startsWith('<!--') && line.trim().endsWith('-->')) continue;

    // Continuation line for in-flight auto-stub (indented, not a new checkbox)
    if (inAutoStubBody && /^\s{2,}\S/.test(line) && !/^\s*-\s*\[/.test(line)) {
      inAutoStubBody.description.push(line.trim());
      continue;
    }

    const checkboxMatch = /^\s*-\s*\[([ x])\]/.exec(line);
    if (!checkboxMatch) {
      flushAutoStub();
      continue;
    }

    flushAutoStub();

    const checked = isCheckedLine(line);
    const path = extractPathFromLine(line);
    const autoStubSlugMatch = AUTO_STUB_RE.exec(line);
    const origin: QueueOrigin = autoStubSlugMatch ? 'auto-stub' : currentOrigin;
    const title = extractTitleFromLine(line, path);
    const description = extractDescriptionFromLine(line);
    const id = `${currentSection}::${path ?? autoStubSlugMatch?.[1] ?? `line-${lineIdx}`}::${lineIdx}`;

    const derivation = deriveStatus(origin, checked, path, ctx);

    const entry: QueueEntry = {
      id,
      section: currentSection,
      origin,
      status: derivation.status,
      path,
      title,
      description,
      confidence: derivation.confidence,
      lastValidated: derivation.lastValidated,
      daysSinceValidated: derivation.daysSinceValidated,
      raw: line,
      checked,
    };

    // Auto-stubs typically have follow-up indented metadata lines; buffer them
    if (origin === 'auto-stub') {
      inAutoStubBody = { entry, description: [] };
    } else {
      entries.push(entry);
    }
  }
  flushAutoStub();

  return entries;
}

/**
 * Remove (or check-off) a queue entry from wiki/_queue.md.
 *
 * Match strategy: locate the line whose `raw` matches the target entryId's
 * original content. Replace with a checked-off + dated version OR delete the
 * line entirely (current behavior: delete, to keep the queue lean — checked
 * entries already had this treatment per the existing 2026-05-15 resolution).
 *
 * Returns { removed: true } when the line was found and removed; false when
 * the entryId no longer matches (file changed underneath, race condition).
 */
function removeQueueEntry(entryId: string): { removed: boolean } {
  if (!pathExists(QUEUE_PATH)) return { removed: false };
  const abs = resolveInRepo(QUEUE_PATH);
  const raw = readFileSync(abs, 'utf-8');
  const lines = raw.split('\n');

  // Reconstruct the entry list with the same logic readQueue uses, but
  // capture (lineIdx, entryId) pairs so we can find the target line.
  const ctx = buildDerivationContext();
  let currentSection = '';
  let currentOrigin: QueueOrigin = 'stub';
  let targetLineIdx = -1;

  let lineIdx = 0;
  for (const line of lines) {
    lineIdx += 1;
    const headingMatch = /^##\s+(.+)$/.exec(line);
    if (headingMatch) {
      currentSection = headingMatch[1].trim();
      currentOrigin = inferOriginFromHeading(currentSection);
      continue;
    }
    if (!currentSection) continue;
    if (line.trim().startsWith('<!--') && line.trim().endsWith('-->')) continue;
    const checkboxMatch = /^\s*-\s*\[([ x])\]/.exec(line);
    if (!checkboxMatch) continue;

    const path = extractPathFromLine(line);
    const autoStubSlugMatch = AUTO_STUB_RE.exec(line);
    const candidateId = `${currentSection}::${path ?? autoStubSlugMatch?.[1] ?? `line-${lineIdx}`}::${lineIdx}`;
    if (candidateId === entryId) {
      targetLineIdx = lineIdx - 1; // back to 0-indexed
      break;
    }
  }

  if (targetLineIdx === -1) {
    // Reference unused once derivation isn't needed for write — keep import warning quiet
    void ctx;
    return { removed: false };
  }

  // For auto-stub entries the entry's logical body spans the checkbox line +
  // any continuation lines (indented, no checkbox) that follow until the next
  // checkbox or blank line. Remove all of them.
  let endIdx = targetLineIdx + 1;
  while (endIdx < lines.length) {
    const next = lines[endIdx];
    if (/^\s*-\s*\[/.test(next)) break;
    if (/^##\s+/.test(next)) break;
    if (next.trim() === '') break;
    if (/^\s{2,}\S/.test(next)) {
      endIdx += 1;
      continue;
    }
    break;
  }

  lines.splice(targetLineIdx, endIdx - targetLineIdx);
  writeFileSync(abs, lines.join('\n'), 'utf-8');
  return { removed: true };
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
  ipcMain.handle('fs:readManifest', async () => readManifest());
  ipcMain.handle('fs:readQueue', async () => readQueue());
  ipcMain.handle('fs:removeQueueEntry', async (_e, entryId: string) => removeQueueEntry(entryId));
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
  ipcMain.handle('meta:authMode', async () => detectAuthMode());
}

export function disposeWatchers(): void {
  for (const w of watchers.values()) w.close().catch(() => {});
  watchers.clear();
}
