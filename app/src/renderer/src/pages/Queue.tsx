import type React from 'react';
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import {
  Play,
  RefreshCw,
  ListChecks,
  Check,
  Circle,
  CircleDashed,
  AlertCircle,
  Clock,
  X,
  ChevronDown,
  ChevronRight,
  Loader2,
  CheckCircle2,
  Square,
} from 'lucide-react';
import type {
  AuthMode,
  ConcurrencyState,
  QueueEntry,
  QueueStatus,
  SkillRequest,
} from '@shared/types';
import { QUEUE_STATUS_ORDER } from '@shared/types';
import { runSkill } from '@/lib/skill';
import { useConcurrency } from '@/store/concurrency';
import { cn } from '@/lib/utils';

type RunStatus = 'running' | 'success' | 'error' | 'cancelled';

/**
 * One active or recently-completed run. Lives in the renderer; identified
 * by a client-generated runId so we can key React + cross-reference rows
 * even before the backend assigns a sessionId.
 *
 * `entryId` is set for entry-scoped skill runs (so a LedgerRow can find
 * its active run); undefined for the standalone wiki-lint button.
 *
 * Runs stay in the array after completion so the user can read the output;
 * dismissed via the per-card X button.
 */
interface ActiveRun {
  runId: string;
  entryId?: string;
  title: string;
  status: RunStatus;
  lines: string[];
  meta?: string;
  collapsed: boolean;
  cancel?: () => void;
  startedAt: number;
}

export function QueuePage(): React.JSX.Element {
  const [entries, setEntries] = useState<QueueEntry[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [runs, setRuns] = useState<ActiveRun[]>([]);
  const [filter, setFilter] = useState<StatusFilter>('open');
  // Default 'oauth' so cost stays hidden until we hear otherwise from main —
  // subscription is the common case and the safer failure mode for a
  // wrong-default error.
  const [authMode, setAuthMode] = useState<AuthMode>('oauth');
  const concurrency = useConcurrency();

  useEffect(() => {
    window.cflt.meta.authMode().then(setAuthMode).catch(() => {
      // Leave as 'oauth' default
    });
  }, []);

  // Debounce refresh so a burst of file-watcher events from parallel runs
  // doesn't hammer the IPC bridge.
  const refreshTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const refresh = useCallback(() => {
    if (refreshTimer.current) clearTimeout(refreshTimer.current);
    refreshTimer.current = setTimeout(() => {
      window.cflt.fs
        .readQueue()
        .then((e) => setEntries(e))
        .catch((e: Error) => setError(e.message));
    }, 150);
  }, []);

  useEffect(() => {
    refresh();
    const dispose = window.cflt.fs.watch(
      [
        'wiki/_queue.md',
        'wiki/_index.md',
        'wiki/_graph.md',
        'wiki/concepts/**/*.md',
        'wiki/patterns/**/*.md',
      ],
      refresh,
    );
    return () => {
      dispose();
      if (refreshTimer.current) clearTimeout(refreshTimer.current);
    };
  }, [refresh]);

  // ─── Run management ────────────────────────────────────────────────

  const updateRun = useCallback(
    (runId: string, patch: Partial<ActiveRun> | ((r: ActiveRun) => Partial<ActiveRun>)) => {
      setRuns((prev) =>
        prev.map((r) => {
          if (r.runId !== runId) return r;
          const apply = typeof patch === 'function' ? patch(r) : patch;
          return { ...r, ...apply };
        }),
      );
    },
    [],
  );

  const dismissRun = useCallback((runId: string) => {
    setRuns((prev) => prev.filter((r) => r.runId !== runId));
  }, []);

  const toggleCollapse = useCallback((runId: string) => {
    setRuns((prev) =>
      prev.map((r) => (r.runId === runId ? { ...r, collapsed: !r.collapsed } : r)),
    );
  }, []);

  const runSkillForEntry = useCallback(
    async (entry: QueueEntry, req: SkillRequest, title: string) => {
      const runId = `run-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
      const handle = runSkill(req);

      // Auto-collapse older entry-scoped runs so the newest is visible
      setRuns((prev) => [
        ...prev.map((r) => (r.entryId ? { ...r, collapsed: true } : r)),
        {
          runId,
          entryId: entry.id,
          title,
          status: 'running',
          lines: [],
          collapsed: false,
          cancel: handle.cancel,
          startedAt: Date.now(),
        },
      ]);

      try {
        for await (const ev of handle.events) {
          switch (ev.type) {
            case 'assistant_text': {
              const pieces = ev.text.split('\n').filter(Boolean);
              updateRun(runId, (r) => ({ lines: [...r.lines, ...pieces] }));
              break;
            }
            case 'tool_use':
              updateRun(runId, (r) => ({
                lines: [...r.lines, `▸ tool_use ${ev.tool.name}`],
              }));
              break;
            case 'error':
              updateRun(runId, (r) => ({
                lines: [...r.lines, `[error] ${ev.message}`],
                status: 'error',
              }));
              break;
            case 'result': {
              const status: RunStatus = ev.result.success ? 'success' : 'error';
              // Subscription (OAuth) users don't see a per-call charge —
              // the CLI's total_cost_usd is API-pricing-equivalent and
              // would mislead. Drop the cost segment in that mode.
              const meta =
                authMode === 'api-key'
                  ? `${ev.result.durationMs}ms · $${ev.result.costUsd.toFixed(4)}`
                  : `${ev.result.durationMs}ms`;
              updateRun(runId, { status, meta, cancel: undefined });
              if (ev.result.success) refresh();
              return;
            }
          }
        }
      } catch (e) {
        updateRun(runId, (r) => ({
          lines: [...r.lines, `[exception] ${(e as Error).message}`],
          status: 'error',
          cancel: undefined,
        }));
      }
    },
    [refresh, updateRun],
  );

  const runWikiLint = useCallback(async () => {
    const runId = `lint-${Date.now()}`;
    const handle = window.cflt.tools.wikiLint({ full: true });

    setRuns((prev) => [
      ...prev,
      {
        runId,
        title: 'python3 tools/wiki-lint.py --full',
        status: 'running',
        lines: [],
        collapsed: false,
        cancel: handle.cancel,
        startedAt: Date.now(),
      },
    ]);

    let appended = false;
    for await (const chunk of handle.output) {
      if (chunk.kind === 'exit') break;
      const text = chunk.text;
      const pieces = text.split('\n').filter(Boolean);
      if (pieces.length === 0) continue;
      appended = true;
      updateRun(runId, (r) => ({ lines: [...r.lines, ...pieces] }));
    }

    const result = await handle.result;
    updateRun(runId, (r) => ({
      status: result.exitCode === 0 ? 'success' : 'error',
      meta: `exit ${result.exitCode}`,
      lines: appended ? r.lines : ['(no output)'],
      cancel: undefined,
    }));
    refresh();
  }, [updateRun, refresh]);

  const removeEntry = useCallback(
    async (entry: QueueEntry) => {
      const res = await window.cflt.fs.removeQueueEntry(entry.id);
      if (!res.removed) {
        setError(
          `Could not remove "${entry.title}" — _queue.md may have changed underneath. Refresh and retry.`,
        );
      }
      refresh();
    },
    [refresh],
  );

  // ─── Derived view state ─────────────────────────────────────────────

  const sorted = useMemo(() => {
    const order = (s: QueueStatus): number => QUEUE_STATUS_ORDER.indexOf(s);
    return [...entries].sort((a, b) => {
      const so = order(a.status) - order(b.status);
      if (so !== 0) return so;
      const sec = a.section.localeCompare(b.section);
      if (sec !== 0) return sec;
      return a.title.localeCompare(b.title);
    });
  }, [entries]);

  const visible = useMemo(() => {
    if (filter === 'all') return sorted;
    if (filter === 'open') return sorted.filter((e) => e.status !== 'published');
    return sorted.filter((e) => e.status === filter);
  }, [sorted, filter]);

  const counts = useMemo(() => {
    const c: Record<QueueStatus | 'total', number> = {
      new: 0, drafted: 0, 'needs-review': 0, validated: 0, stale: 0, published: 0,
      total: entries.length,
    };
    for (const e of entries) c[e.status] += 1;
    return c;
  }, [entries]);

  // Map entryId → active run (only in-flight runs count for the row badge)
  const activeRunByEntry = useMemo(() => {
    const map = new Map<string, ActiveRun>();
    for (const r of runs) {
      if (r.entryId && r.status === 'running') map.set(r.entryId, r);
    }
    return map;
  }, [runs]);

  return (
    <div className="grid h-full grid-cols-[minmax(0,1fr)_22rem] gap-4 overflow-hidden p-4">
      <div className="flex min-h-0 flex-col gap-3">
        <header className="flex items-center justify-between rounded-md border border-border bg-muted/20 px-3 py-2">
          <div className="flex items-center gap-2">
            <ListChecks className="h-4 w-4 text-cflt-blue" />
            <h1 className="text-sm font-semibold tracking-tight text-foreground">
              Wiki Queue Ledger
            </h1>
            <span className="text-[11px] text-muted-foreground">
              {visible.length} of {counts.total} entries
            </span>
            <ConcurrencyBadge state={concurrency} />
          </div>
          <div className="flex items-center gap-1.5">
            <FilterDropdown filter={filter} counts={counts} onChange={setFilter} />
            <button
              type="button"
              onClick={runWikiLint}
              className="flex items-center gap-1 rounded bg-cflt-blue/15 px-2.5 py-1 text-[11px] uppercase tracking-wide text-cflt-blue hover:bg-cflt-blue/25"
            >
              <Play className="h-3 w-3" />
              run /wiki:lint
            </button>
            <button
              type="button"
              onClick={refresh}
              className="rounded p-1 text-muted-foreground hover:bg-muted hover:text-foreground"
              title="Refresh from disk"
            >
              <RefreshCw className="h-3 w-3" />
            </button>
          </div>
        </header>
        {error && (
          <div className="flex items-start justify-between rounded border border-danger/40 bg-danger/10 p-3 text-xs text-danger">
            <span className="break-words">{error}</span>
            <button
              onClick={() => setError(null)}
              className="ml-2 opacity-60 hover:opacity-100"
            >
              <X className="h-3 w-3" />
            </button>
          </div>
        )}
        <div className="min-h-0 flex-1 overflow-auto rounded-md border border-border">
          {visible.length === 0 ? (
            <div className="flex h-full items-center justify-center text-sm text-muted-foreground">
              {entries.length === 0
                ? 'wiki/_queue.md is empty.'
                : `No entries match filter "${filter}".`}
            </div>
          ) : (
            <ul className="divide-y divide-border">
              {visible.map((entry) => (
                <LedgerRow
                  key={entry.id}
                  entry={entry}
                  activeRun={activeRunByEntry.get(entry.id)}
                  onRunSkill={runSkillForEntry}
                  onRemove={removeEntry}
                />
              ))}
            </ul>
          )}
        </div>
      </div>
      <RunStack
        runs={runs}
        onDismiss={dismissRun}
        onToggleCollapse={toggleCollapse}
      />
    </div>
  );
}

// ─── Ledger row ────────────────────────────────────────────────────────

function LedgerRow({
  entry,
  activeRun,
  onRunSkill,
  onRemove,
}: {
  entry: QueueEntry;
  activeRun?: ActiveRun;
  onRunSkill: (entry: QueueEntry, req: SkillRequest, title: string) => void;
  onRemove: (entry: QueueEntry) => void;
}): React.JSX.Element {
  const action = inferAction(entry);
  const inFlight = !!activeRun;

  const dispatchAction = (): void => {
    if (!action || inFlight) return;
    if (action.kind === 'remove') {
      onRemove(entry);
      return;
    }
    const args = entry.path ?? entry.title;
    const req: SkillRequest =
      action.skill === '/wiki:ingest'
        ? { kind: 'wiki:ingest', args }
        : { kind: 'wiki:validate', args };
    onRunSkill(entry, req, `${action.skill}${args ? ` ${args}` : ''}`);
  };

  return (
    <li className="group flex items-start gap-3 bg-background/40 px-3 py-2 hover:bg-muted/20">
      <StatusPill status={entry.status} />
      <div className="min-w-0 flex-1">
        <div className="flex items-baseline gap-2">
          <span
            className="truncate text-[12px] font-medium text-foreground/90"
            title={entry.title}
          >
            {entry.title}
          </span>
          <OriginTag origin={entry.origin} />
          {entry.lastValidated && (
            <span
              className="font-mono text-[10px] text-muted-foreground"
              title={`Last validated ${entry.lastValidated}`}
            >
              {entry.lastValidated}
              {entry.daysSinceValidated !== undefined && (
                <span
                  className={cn(
                    'ml-1',
                    entry.daysSinceValidated > 90 ? 'text-warning' : '',
                  )}
                >
                  ({entry.daysSinceValidated}d)
                </span>
              )}
            </span>
          )}
        </div>
        {entry.path && (
          <div
            className="truncate font-mono text-[10px] text-muted-foreground"
            title={entry.path}
          >
            {entry.path}
          </div>
        )}
        {entry.description && (
          <div className="mt-0.5 line-clamp-2 text-[11px] text-muted-foreground/80">
            {entry.description}
          </div>
        )}
      </div>
      {inFlight ? (
        <RowRunBadge run={activeRun!} />
      ) : (
        action && (
          <button
            type="button"
            onClick={dispatchAction}
            className={cn(
              'shrink-0 self-center rounded px-2 py-1 text-[10px] uppercase tracking-wide',
              action.kind === 'remove'
                ? 'bg-success/15 text-success hover:bg-success/25'
                : action.skill === '/wiki:ingest'
                  ? 'bg-warning/15 text-warning hover:bg-warning/25'
                  : 'bg-cflt-blue/15 text-cflt-blue hover:bg-cflt-blue/25',
            )}
          >
            {action.label}
          </button>
        )
      )}
    </li>
  );
}

function RowRunBadge({ run }: { run: ActiveRun }): React.JSX.Element {
  return (
    <div className="flex shrink-0 items-center gap-1 self-center rounded bg-cflt-blue/15 px-1.5 py-1 text-[10px] uppercase tracking-wide text-cflt-blue">
      <Loader2 className="h-2.5 w-2.5 animate-spin" />
      running
      {run.cancel && (
        <button
          type="button"
          onClick={() => run.cancel?.()}
          className="ml-1 rounded bg-danger/15 px-1 py-px text-danger hover:bg-danger/25"
          title="Cancel"
        >
          <Square className="h-2 w-2" />
        </button>
      )}
    </div>
  );
}

// ─── Status pill / origin tag ──────────────────────────────────────────

function StatusPill({ status }: { status: QueueStatus }): React.JSX.Element {
  const meta = STATUS_META[status];
  const Icon = meta.icon;
  return (
    <span
      className={cn(
        'mt-0.5 flex shrink-0 items-center gap-1 rounded-full px-1.5 py-0.5 text-[9px] uppercase tracking-wider',
        meta.classes,
      )}
      title={meta.tooltip}
    >
      <Icon className="h-2.5 w-2.5" />
      {status}
    </span>
  );
}

function OriginTag({ origin }: { origin: QueueEntry['origin'] }): React.JSX.Element {
  return (
    <span className="rounded bg-muted/40 px-1 py-px font-mono text-[9px] uppercase tracking-wider text-muted-foreground">
      {origin}
    </span>
  );
}

// ─── Concurrency badge ────────────────────────────────────────────────

function ConcurrencyBadge({ state }: { state: ConcurrencyState }): React.JSX.Element {
  const { mutatingActive, nonMutatingActive, queueDepth } = state;
  const anyActive = mutatingActive + nonMutatingActive + queueDepth > 0;
  return (
    <span
      className={cn(
        'rounded bg-muted/30 px-1.5 py-0.5 font-mono text-[10px]',
        anyActive ? 'text-cflt-blue' : 'text-muted-foreground/70',
      )}
      title="Mutating slots (max 1) · Non-mutating slots (max 3) · Queued"
    >
      {mutatingActive}/1 mut · {nonMutatingActive}/3 read
      {queueDepth > 0 && <span className="ml-1 text-warning">· {queueDepth} queued</span>}
    </span>
  );
}

// ─── Filter dropdown ──────────────────────────────────────────────────

type StatusFilter = QueueStatus | 'all' | 'open';

function FilterDropdown({
  filter,
  counts,
  onChange,
}: {
  filter: StatusFilter;
  counts: Record<QueueStatus | 'total', number>;
  onChange: (f: StatusFilter) => void;
}): React.JSX.Element {
  const options: { value: StatusFilter; label: string; count: number }[] = [
    { value: 'open', label: 'Open (excl. published)', count: counts.total - counts.published },
    { value: 'all', label: 'All', count: counts.total },
    { value: 'new', label: 'new', count: counts.new },
    { value: 'drafted', label: 'drafted', count: counts.drafted },
    { value: 'needs-review', label: 'needs-review', count: counts['needs-review'] },
    { value: 'validated', label: 'validated', count: counts.validated },
    { value: 'stale', label: 'stale', count: counts.stale },
    { value: 'published', label: 'published', count: counts.published },
  ];
  return (
    <select
      value={filter}
      onChange={(e) => onChange(e.target.value as StatusFilter)}
      className="rounded border border-border bg-background px-2 py-1 text-[11px] text-foreground"
    >
      {options.map((opt) => (
        <option key={opt.value} value={opt.value}>
          {opt.label} ({opt.count})
        </option>
      ))}
    </select>
  );
}

// ─── Run stack (right column) ─────────────────────────────────────────

function RunStack({
  runs,
  onDismiss,
  onToggleCollapse,
}: {
  runs: ActiveRun[];
  onDismiss: (runId: string) => void;
  onToggleCollapse: (runId: string) => void;
}): React.JSX.Element {
  const activeCount = runs.filter((r) => r.status === 'running').length;
  return (
    <div className="flex min-h-0 flex-col gap-2 overflow-auto">
      <div className="flex items-center justify-between rounded-md border border-border bg-muted/20 px-3 py-1.5 text-[11px] text-muted-foreground">
        <span>Runs ({activeCount} active{runs.length > activeCount ? ` · ${runs.length - activeCount} done` : ''})</span>
        {runs.length > 0 && (
          <button
            type="button"
            onClick={() => runs.filter((r) => r.status !== 'running').forEach((r) => onDismiss(r.runId))}
            className="text-[10px] uppercase tracking-wide text-muted-foreground hover:text-foreground"
            title="Dismiss completed runs"
          >
            clear done
          </button>
        )}
      </div>
      {runs.length === 0 ? (
        <div className="flex flex-1 items-center justify-center rounded-md border border-dashed border-border text-xs text-muted-foreground">
          Run output appears here.
        </div>
      ) : (
        runs.map((r) => (
          <RunCard key={r.runId} run={r} onDismiss={onDismiss} onToggleCollapse={onToggleCollapse} />
        ))
      )}
    </div>
  );
}

function RunCard({
  run,
  onDismiss,
  onToggleCollapse,
}: {
  run: ActiveRun;
  onDismiss: (runId: string) => void;
  onToggleCollapse: (runId: string) => void;
}): React.JSX.Element {
  const bodyRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (run.status === 'running' && !run.collapsed && bodyRef.current) {
      bodyRef.current.scrollTop = bodyRef.current.scrollHeight;
    }
  }, [run.lines, run.status, run.collapsed]);

  return (
    <div className="shrink-0 rounded-md border border-border bg-cflt-ink/60">
      <header className="flex items-center justify-between gap-2 border-b border-border px-2 py-1.5 text-[11px]">
        <button
          type="button"
          onClick={() => onToggleCollapse(run.runId)}
          className="flex min-w-0 flex-1 items-center gap-1.5 text-left"
          title={run.collapsed ? 'Expand' : 'Collapse'}
        >
          {run.collapsed ? (
            <ChevronRight className="h-3 w-3 shrink-0 text-muted-foreground" />
          ) : (
            <ChevronDown className="h-3 w-3 shrink-0 text-muted-foreground" />
          )}
          <RunStatusIcon status={run.status} />
          <span className="truncate font-mono text-foreground/90" title={run.title}>
            {run.title}
          </span>
          {run.meta && (
            <span className="shrink-0 rounded bg-muted px-1.5 py-0.5 font-mono text-[10px] text-muted-foreground">
              {run.meta}
            </span>
          )}
        </button>
        <div className="flex shrink-0 items-center gap-1">
          {run.status === 'running' && run.cancel && (
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                run.cancel?.();
              }}
              className="flex items-center gap-1 rounded bg-danger/15 px-1.5 py-0.5 text-[10px] uppercase tracking-wide text-danger hover:bg-danger/25"
            >
              <Square className="h-2.5 w-2.5" />
              cancel
            </button>
          )}
          {run.status !== 'running' && (
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                onDismiss(run.runId);
              }}
              className="rounded p-0.5 text-muted-foreground hover:bg-muted hover:text-foreground"
              title="Dismiss"
            >
              <X className="h-3 w-3" />
            </button>
          )}
        </div>
      </header>
      {!run.collapsed && (
        <div
          ref={bodyRef}
          className="max-h-48 overflow-auto p-2 font-mono text-[10.5px] leading-relaxed text-muted-foreground"
        >
          {run.lines.length === 0 ? (
            <div className="text-muted-foreground/60">no output yet…</div>
          ) : (
            run.lines.map((l, i) => (
              <div key={i} className="whitespace-pre-wrap">
                {l}
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
}

function RunStatusIcon({ status }: { status: RunStatus }): React.JSX.Element {
  switch (status) {
    case 'running':
      return <Loader2 className="h-3 w-3 shrink-0 animate-spin text-cflt-blue" />;
    case 'success':
      return <CheckCircle2 className="h-3 w-3 shrink-0 text-success" />;
    case 'error':
      return <AlertCircle className="h-3 w-3 shrink-0 text-danger" />;
    case 'cancelled':
      return <AlertCircle className="h-3 w-3 shrink-0 text-warning" />;
  }
}

// ─── Status / action metadata ──────────────────────────────────────────

interface StatusMeta {
  icon: typeof Circle;
  classes: string;
  tooltip: string;
}

const STATUS_META: Record<QueueStatus, StatusMeta> = {
  new: {
    icon: Circle,
    classes: 'bg-muted/30 text-muted-foreground',
    tooltip: 'No article yet — needs /wiki:ingest',
  },
  drafted: {
    icon: CircleDashed,
    classes: 'bg-warning/20 text-warning',
    tooltip: 'Article exists with confidence:medium or ⚠️ Stub marker — needs /wiki:validate',
  },
  'needs-review': {
    icon: AlertCircle,
    classes: 'bg-warning/20 text-warning',
    tooltip: '⚠️ unverified claim still present — needs /wiki:validate',
  },
  validated: {
    icon: Check,
    classes: 'bg-cflt-blue/20 text-cflt-blue',
    tooltip:
      'Article has confidence:high + recent last_validated — can be removed from queue',
  },
  stale: {
    icon: Clock,
    classes: 'bg-warning/30 text-warning',
    tooltip: 'Validated >90 days ago — re-validate',
  },
  published: {
    icon: Check,
    classes: 'bg-success/20 text-success',
    tooltip: 'Validated + indexed + linked — remove from queue',
  },
};

interface RowAction {
  kind: 'skill' | 'remove';
  skill?: '/wiki:ingest' | '/wiki:validate';
  label: string;
}

function inferAction(entry: QueueEntry): RowAction | null {
  switch (entry.status) {
    case 'new':
      return { kind: 'skill', skill: '/wiki:ingest', label: 'Ingest' };
    case 'drafted':
      return { kind: 'skill', skill: '/wiki:validate', label: 'Validate' };
    case 'needs-review':
      return { kind: 'skill', skill: '/wiki:validate', label: 'Validate' };
    case 'stale':
      return { kind: 'skill', skill: '/wiki:validate', label: 'Re-validate' };
    case 'validated':
      return { kind: 'remove', label: 'Promote' };
    case 'published':
      return { kind: 'remove', label: 'Remove' };
    default:
      return null;
  }
}
