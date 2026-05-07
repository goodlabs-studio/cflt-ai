// Single source of truth for IPC types between main and renderer.
// Phase A scope: fs read API only. Skill/tool/confirm/mcp surfaces stubbed.

export interface WikiArticleFrontmatter {
  title?: string;
  tags?: string[];
  sources?: string[];
  related?: string[];
  confidence?: 'high' | 'medium' | 'low';
  last_updated?: string;
  last_validated?: string;
  [key: string]: unknown;
}

export interface WikiArticle {
  path: string; // repo-relative, e.g. "wiki/concepts/exactly-once-semantics.md"
  frontmatter: WikiArticleFrontmatter;
  body: string; // markdown body without frontmatter
}

export interface WikiNode {
  name: string; // display name (filename without .md, or section name)
  path: string; // repo-relative
  type: 'section' | 'article';
  children?: WikiNode[];
}

export interface GraphEdge {
  source: string; // e.g. "concepts/sla-tiers"
  target: string;
  relationship: string;
}

export interface QueueSection {
  heading: string; // verbatim section name from _queue.md
  entries: string[]; // raw markdown lines under the section
}

export interface ActivityEntry {
  timestamp: string; // ISO
  skill: string;
  overlay?: string;
  input?: string;
  output?: string;
  canonStack?: string;
  raw: string; // full markdown block for fallback display
}

export interface IncidentMeta {
  path: string;
  title?: string;
  date?: string;
}

export interface ReportMeta {
  slug: string;
  path: string;
  date?: string;
  sourceSkill?: string;
  claimsChecked?: number;
  claimsCorrected?: number;
  claimsUnverifiable?: number;
}

export interface PlanMeta {
  slug: string;
  path: string;
  date?: string;
  artifact?: string;
}

export interface PlanDoc {
  meta: PlanMeta;
  body: string;
}

export type FsEvent =
  | { kind: 'add'; path: string }
  | { kind: 'change'; path: string }
  | { kind: 'unlink'; path: string };

export type WatchUnsubscribe = () => void;

export interface CfltFsAPI {
  readWiki(path: string): Promise<WikiArticle>;
  listWikiTree(): Promise<WikiNode[]>;
  readGraph(): Promise<GraphEdge[]>;
  readQueue(): Promise<QueueSection[]>;
  readActivity(month?: string): Promise<ActivityEntry[]>;
  listIncidents(): Promise<IncidentMeta[]>;
  listReports(): Promise<ReportMeta[]>;
  readReport(slug: string): Promise<string>;
  listPlans(): Promise<PlanMeta[]>;
  readPlan(path: string): Promise<PlanDoc>;
  listOverlays(): Promise<string[]>;
  activeLayers(): Promise<string[]>;
  watch(globs: string[], cb: (event: FsEvent) => void): WatchUnsubscribe;
}

// Future surfaces (stubbed in Phase A; expanded in B-E)
export interface CfltSkillAPI {
  // run(req): { events, cancel, result } — Phase B
  // listProfiles(): Promise<Profile[]> — Phase D
}
export interface CfltToolAPI {
  // wikiLint, wikiSearch, wikiStats, reviewToDocx — Phase B
}
export interface CfltConfirmAPI {
  // onRequest, respond — Phase D
}
export interface CfltMcpAPI {
  // health() — Phase E
}

export interface CfltAPI {
  fs: CfltFsAPI;
  skill: CfltSkillAPI;
  tools: CfltToolAPI;
  confirm: CfltConfirmAPI;
  mcp: CfltMcpAPI;
  /** Surface info for the titlebar; populated as features come online. */
  meta: {
    repoRoot(): Promise<string>;
    appVersion(): Promise<string>;
  };
}

declare global {
  interface Window {
    cflt: CfltAPI;
  }
}
