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

// ─── Skill streaming (Phase B) ────────────────────────────────────────────

export type ClaudeRoute = 'wiki' | 'mcp' | 'deep';
export type AskMode = 'ephemeral' | 'report' | 'reconsolidate';

export interface McpServerStatus {
  name: string;
  status: 'connected' | 'failed' | 'needs-auth' | 'unknown';
}

export interface InitInfo {
  cwd: string;
  model: string;
  tools: string[];
  mcpServers: McpServerStatus[];
  sessionId: string;
}

export interface ToolUseEvent {
  id: string;
  name: string;
  input: unknown;
}

export interface ToolResultEvent {
  toolUseId: string;
  output: unknown;
  isError?: boolean;
}

export interface RateLimitEvent {
  status: string; // "allowed" | "throttled" | ...
  resetsAt?: number;
  isUsingOverage?: boolean;
}

export interface SkillResult {
  success: boolean;
  text: string;
  durationMs: number;
  costUsd: number;
  inputTokens: number;
  outputTokens: number;
  sessionId?: string;
}

/**
 * Normalized event stream from a claude subprocess. Discriminated union for
 * exhaustive handling. Unknown raw events fall through to `raw` so the UI
 * can degrade without crashing on CLI version drift.
 */
export type StreamEvent =
  | { type: 'init'; info: InitInfo }
  | { type: 'assistant_text'; text: string; messageId: string }
  | { type: 'tool_use'; tool: ToolUseEvent }
  | { type: 'tool_result'; result: ToolResultEvent }
  | { type: 'route'; route: ClaudeRoute }
  | { type: 'rate_limit'; info: RateLimitEvent }
  | { type: 'system'; subtype: string; data: Record<string, unknown> }
  | { type: 'result'; result: SkillResult }
  | { type: 'error'; message: string; recoverable?: boolean }
  | { type: 'raw'; raw: Record<string, unknown> };

/**
 * Skill invocation requests. Flat shape matched on `kind` for dispatch.
 * Phase B.1 implements `ask` and the `wiki:*` family. Other kinds are
 * accepted by IPC but invoked unchanged.
 */
export type SkillRequest =
  | {
      kind: 'ask';
      query: string;
      mode: AskMode;
      forceRoute?: ClaudeRoute;
    }
  | {
      kind: 'review';
      docPaths: string[];
      output?: 'md' | 'docx' | 'both';
      overlay?: string;
    }
  | {
      kind:
        | 'wiki:lint'
        | 'wiki:validate'
        | 'wiki:ingest'
        | 'wiki:evaluate'
        | 'wiki:recommend';
      args?: string;
    }
  | { kind: 'dsp:plan'; request: string; overlay?: string; gateBypass?: string[] }
  | {
      kind: 'dsp:apply';
      planPath: string;
      profile: 'read-only' | 'engineer' | 'break-glass';
      overlay?: string;
      operator?: string;
    };

export interface RunHandle {
  sessionId: string;
  events: AsyncIterable<StreamEvent>;
  cancel(): void;
  result: Promise<SkillResult>;
}

export interface Profile {
  name: string;
  allowedOperations: string[];
  description?: string;
}

export interface CfltSkillAPI {
  run(req: SkillRequest): RunHandle;
  listProfiles(): Promise<Profile[]>;
}

export interface SearchHit {
  path: string;       // repo-relative wiki path
  score: number;      // raw score from wiki-search.py
  preview: string;    // title or first-match line
}

export interface WikiStatsBucket {
  name: string;
  count: number;
}

export interface WikiStats {
  articles: number;
  totalWords: number;
  rawSources: number;
  bySection: WikiStatsBucket[];
  byConfidence: WikiStatsBucket[];
  topTags: WikiStatsBucket[];
}

export interface ToolRunHandle {
  /** AsyncIterable yielding raw stdout chunks plus a terminal {kind:'exit'} */
  output: AsyncIterable<ToolOutputChunk>;
  cancel(): void;
  /** Resolves with exit code when subprocess closes */
  result: Promise<{ exitCode: number; stdout: string; stderr: string }>;
}

export type ToolOutputChunk =
  | { kind: 'stdout'; text: string }
  | { kind: 'stderr'; text: string }
  | { kind: 'exit'; code: number };

export interface CfltToolAPI {
  /** Streaming wiki lint. Returns a handle whose output emits stdout chunks. */
  wikiLint(args?: { full?: boolean; fix?: boolean }): ToolRunHandle;
  wikiSearch(query: string): Promise<SearchHit[]>;
  wikiStats(): Promise<WikiStats>;
  /** Returns the absolute output .docx path on success. */
  reviewToDocx(reportPath: string): Promise<string>;
}

// ─── Review parsing (Phase C) ─────────────────────────────────────────────

export type ClaimCategory =
  | 'config_value'
  | 'behavior_assertion'
  | 'architecture_choice'
  | 'metric_sla'
  | 'comparison';

export type ClaimVerdict = 'Confirmed' | 'Corrected' | 'Unverifiable' | 'Pending';

export interface ReviewClaim {
  id: string; // e.g., "deck-1"
  sourceFile: string;
  sourceSection: string;
  category: ClaimCategory;
  text: string;
  /** Filled in after Step 5 validation table is rendered. Undefined while
   * the YAML block is the only thing parsed. */
  wikiSource?: string;
  mcpSource?: string;
  verdict?: ClaimVerdict;
}

export interface ParsedReview {
  /** Title from H1; empty if not yet emitted. */
  title: string;
  claims: ReviewClaim[];
  /** True once the model has emitted the closing ``` of the claims YAML. */
  claimsComplete: boolean;
  /** True once the ## Claim Validation section has been rendered. */
  validationComplete: boolean;
}

// ─── File dialog (Phase C) ────────────────────────────────────────────────

export interface CfltDialogAPI {
  /** Open a file picker for review document input. Returns absolute paths. */
  openReviewFiles(): Promise<string[]>;
}

// ─── Concurrency guard (Phase B.2) ────────────────────────────────────────

export type SkillClass = 'mutating' | 'non-mutating';

export interface ConcurrencyState {
  /** Number of mutating runs currently active. Max 1. */
  mutatingActive: number;
  /** Number of non-mutating runs currently active. Max 3. */
  nonMutatingActive: number;
  /** Pending runs waiting for a slot (FIFO). */
  queueDepth: number;
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
  dialog: CfltDialogAPI;
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
