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

/**
 * One capability entry from fsi-dsp MANIFEST.yaml — the stable wiki↔asset
 * contract. Patterns reference these via `fsi-dsp://<id>` URIs in frontmatter
 * `sources`; the renderer resolves those URIs against this list.
 */
export interface ManifestEntry {
  id: string; // stable capability id, e.g. "role/cp_dr_mm2"
  type: string; // ansible-role | terraform-module | scenario | script | …
  name: string;
  path: string; // repo-relative within fsi-dsp
  description: string;
}

/**
 * Queue entry status — derived at read-time by cross-referencing _queue.md
 * against the wiki tree. Never stored in _queue.md. Order matters for sort.
 *
 * Lifecycle: new → drafted → (needs-review for claim-type) → validated → published
 *            (or stale if validated > DECAY_DAYS old)
 */
export const QUEUE_STATUS_ORDER = [
  'new',
  'drafted',
  'needs-review',
  'validated',
  'stale',
  'published',
] as const;
export type QueueStatus = (typeof QUEUE_STATUS_ORDER)[number];

/**
 * Where the queue entry came from. Drives action-button labeling and the
 * derivation rules (claim entries point at a marker inside an existing file,
 * stub/auto-stub entries point at a path that should become a wiki article).
 */
export type QueueOrigin = 'stub' | 'auto-stub' | 'claim' | 'lint' | 'candidate';

export interface QueueEntry {
  /** Stable identifier for write-back. Derived from path + section + line index. */
  id: string;
  /** Source section heading (kept for grouping/audit). */
  section: string;
  /** Origin tag — drives action verb + derivation. */
  origin: QueueOrigin;
  /** Derived status (see derivation table in J.1 plan). */
  status: QueueStatus;
  /** Target wiki path when present (e.g., "wiki/concepts/foo.md"). Claim entries put the host article path here. */
  path?: string;
  /** Display title — extracted markdown link text, or slug, or raw line. */
  title: string;
  /** Free-text description from the queue line (everything after the path/em-dash). */
  description?: string;
  /** Article frontmatter `confidence` when path resolves to an existing file. */
  confidence?: 'high' | 'medium' | 'low';
  /** ISO date string from frontmatter `last_validated`. */
  lastValidated?: string;
  /** Days since `last_validated` (for stale detection). Undefined if no validated date. */
  daysSinceValidated?: number;
  /** Verbatim source line from _queue.md (for the activity panel + write-back match). */
  raw: string;
  /** True when the entry's checkbox is already `[x]`. */
  checked: boolean;
}

/**
 * @deprecated J.1 ledger redesign — kept only for unused callers during transition.
 * Use QueueEntry[] from readQueue() instead.
 */
export interface QueueSection {
  heading: string;
  entries: string[];
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
  readManifest(): Promise<ManifestEntry[]>;
  readQueue(): Promise<QueueEntry[]>;
  removeQueueEntry(entryId: string): Promise<{ removed: boolean }>;
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
  status: 'connected' | 'failed' | 'needs-auth' | 'pending' | 'unknown';
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
      /** When true, FRANZ has already shown a native confirmation modal
       * and captured the operator's decision. The skill's Step 6 skips its
       * own AskUserQuestion and records `confirmation_source="pre-confirmed"`. */
      preConfirmed?: boolean;
      /** Required when preConfirmed is true AND profile is break-glass —
       * the override reason captured by the modal. */
      reason?: string;
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

// ─── Act-rail / dsp:apply (Phase D.2) ─────────────────────────────────────

export type ApplyProfile = 'read-only' | 'engineer' | 'break-glass';

export interface PlanSummary {
  slug: string;
  path: string;
  date?: string;
  artifact?: SelectedArtifact;
  /** "key: value" pairs from the Arguments section, in source order. */
  arguments?: Array<{ key: string; value: string }>;
  /** GateInfo[] parsed from the saved plan's Gate Results table. */
  gates?: GateInfo[];
  /** Canon Compliance section as raw markdown so the modal can render. */
  canonCompliance?: string;
  /** Provenance line ("Canon stack: ...") when present. */
  provenance?: string;
}

export interface ApplyConfirmation {
  confirmed: boolean;
  /** Required when profile=break-glass. */
  reason?: string;
}

// ─── Act-rail / dsp:plan (Phase D.1) ──────────────────────────────────────

export const GATE_NAMES = [
  'canon_compliance',
  'fsi_dsp_coverage',
  'confluent_docs_schema',
  'mcp_confluent_state',
] as const;
export type GateName = (typeof GATE_NAMES)[number];

export type GateState = 'pending' | 'running' | 'pass' | 'fail' | 'skipped';

export interface GateInfo {
  name: GateName;
  state: GateState;
  detail?: string;
  evidence?: string[];
}

export interface SelectedArtifact {
  id: string;        // e.g. "module/topic"
  path?: string;
  description?: string;
}

export interface ParsedPlan {
  gates: GateInfo[];
  /** True once a Gate Results table has been parsed end-to-end. */
  gatesComplete: boolean;
  artifact?: SelectedArtifact;
  /** Provenance footer "Gate results:" line, if seen. */
  footerGateLine?: string;
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
  /**
   * Run an out-of-band health probe against all MCP servers configured
   * in .mcp.json. Zero LLM cost — shells `claude mcp list`. Returns the
   * latest snapshot and updates the renderer's MCP slice as a side
   * effect.
   */
  health(): Promise<McpServerStatus[]>;
}

// ─── Settings (Phase E) ──────────────────────────────────────────────────

export interface UserConfig {
  maxBudgetUsd: number;
  defaultAskMode: AskMode;
  defaultApplyProfile: ApplyProfile;
  defaultOverlay: string;
  /** Arbitrary KEY=value pairs FRANZ injects into every subprocess env
   * and writes to a managed file at {userData}/mcp.env. CONFLUENT_MCP_ENV_FILE
   * is auto-set to that path so mcp-confluent picks them up. */
  mcpEnvVars?: Record<string, string>;
}

export interface CfltConfigAPI {
  get(): Promise<UserConfig>;
  set(patch: Partial<UserConfig>): Promise<UserConfig>;
}

/**
 * How the Claude Code CLI is authenticated. Drives whether the UI shows
 * per-run cost figures — irrelevant under OAuth (subscription).
 */
export type AuthMode = 'oauth' | 'api-key';

export interface CfltAPI {
  fs: CfltFsAPI;
  skill: CfltSkillAPI;
  tools: CfltToolAPI;
  confirm: CfltConfirmAPI;
  mcp: CfltMcpAPI;
  dialog: CfltDialogAPI;
  config: CfltConfigAPI;
  /** Surface info for the titlebar; populated as features come online. */
  meta: {
    repoRoot(): Promise<string>;
    appVersion(): Promise<string>;
    /** OAuth (claude.ai subscription) vs API key. Cached after first call. */
    authMode(): Promise<AuthMode>;
  };
}

declare global {
  interface Window {
    cflt: CfltAPI;
  }
}
