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
} from 'lucide-react';
import type { QueueEntry, QueueStatus, SkillRequest } from '@shared/types';
import { QUEUE_STATUS_ORDER } from '@shared/types';
import { runSkill } from '@/lib/skill';
import { RunPanel, type RunPanelStatus } from '@/components/RunPanel';
import { cn } from '@/lib/utils';

interface RunPanelState {
  title: string;
  status: RunPanelStatus;
  lines: string[];
  meta?: string;
  cancel?: () => void;
}

type StatusFilter = QueueStatus | 'all' | 'open';

export function QueuePage(): React.JSX.Element {
  const [entries, setEntries] = useState<QueueEntry[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [activePanel, setActivePanel] = useState<RunPanelState | null>(null);
  const [filter, setFilter] = useState<StatusFilter>('open');
  const cancelRef = useRef<(() => void) | null>(null);

  const refresh = useCallback(() => {
    window.cflt.fs
      .readQueue()
      .then((e) => setEntries(e))
      .catch((e: Error) => setError(e.message));
  }, []);

  useEffect(() => {
    refresh();
    const dispose = window.cflt.fs.watch(['wiki/_queue.md', 'wiki/_index.md', 'wiki/_graph.md', 'wiki/concepts/**/*.md', 'wiki/patterns/**/*.md'], refresh);
    return dispose;
  }, [refresh]);

  const setPanel = useCallback((next: RunPanelState | null) => {
    setActivePanel(next);
  }, []);

  const runWikiLint = useCallback(async () => {
    if (cancelRef.current) cancelRef.current();
    const lines: string[] = [];
    setPanel({
      title: 'python3 tools/wiki-lint.py --full',
      status: 'running',
      lines,
    });

    const handle = window.cflt.tools.wikiLint({ full: true });
    cancelRef.current = handle.cancel;

    let appended = false;
    for await (const chunk of handle.output) {
      if (chunk.kind === 'exit') break;
      const text = chunk.text;
      for (const piece of text.split('\n')) {
        if (piece) lines.push(piece);
      }
      appended = true;
      setPanel({
        title: 'python3 tools/wiki-lint.py --full',
        status: 'running',
        lines: [...lines],
      });
    }

    const result = await handle.result;
    cancelRef.current = null;
    setPanel({
      title: 'python3 tools/wiki-lint.py --full',
      status: result.exitCode === 0 ? 'success' : 'error',
      lines: appended ? [...lines] : ['(no output)'],
      meta: `exit ${result.exitCode}`,
    });
    refresh();
  }, [setPanel, refresh]);

  const runSkillForEntry = useCallback(
    async (entry: QueueEntry, req: SkillRequest, title: string) => {
      if (cancelRef.current) cancelRef.current();
      const lines: string[] = [];
      setPanel({ title, status: 'running', lines });

      const handle = runSkill(req);
      cancelRef.current = handle.cancel;

      for await (const ev of handle.events) {
        switch (ev.type) {
          case 'assistant_text':
            for (const piece of ev.text.split('\n')) {
              if (piece) lines.push(piece);
            }
            setPanel({ title, status: 'running', lines: [...lines] });
            break;
          case 'tool_use':
            lines.push(`▸ tool_use ${ev.tool.name}`);
            setPanel({ title, status: 'running', lines: [...lines] });
            break;
          case 'error':
            lines.push(`[error] ${ev.message}`);
            setPanel({ title, status: 'error', lines: [...lines] });
            break;
          case 'result': {
            cancelRef.current = null;
            const status: RunPanelStatus = ev.result.success ? 'success' : 'error';
            setPanel({
              title,
              status,
              lines: [...lines],
              meta: `${ev.result.durationMs}ms · $${ev.result.costUsd.toFixed(4)}`,
            });
            // Critical J.1 fix: refresh immediately on success so derived
            // status picks up the new article without waiting on chokidar.
            if (ev.result.success) refresh();
            return;
          }
        }
      }
    },
    [setPanel, refresh],
  );

  const removeEntry = useCallback(
    async (entry: QueueEntry) => {
      const res = await window.cflt.fs.removeQueueEntry(entry.id);
      if (!res.removed) {
        setError(`Could not remove "${entry.title}" — _queue.md may have changed underneath. Refresh and retry.`);
      }
      refresh();
    },
    [refresh],
  );

  // Sort by status order ASC, then by section, then by title
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
      new: 0, drafted: 0, 'needs-review': 0, validated: 0, stale: 0, published: 0, total: entries.length,
    };
    for (const e of entries) c[e.status] += 1;
    return c;
  }, [entries]);

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
            <button onClick={() => setError(null)} className="ml-2 opacity-60 hover:opacity-100">
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
                  onRunSkill={runSkillForEntry}
                  onRemove={removeEntry}
                />
              ))}
            </ul>
          )}
        </div>
      </div>
      <div className="min-h-0">
        {activePanel ? (
          <RunPanel
            title={activePanel.title}
            status={activePanel.status}
            lines={activePanel.lines}
            meta={activePanel.meta}
            onCancel={
              activePanel.status === 'running' && cancelRef.current
                ? () => cancelRef.current?.()
                : undefined
            }
            onClose={() => setPanel(null)}
          />
        ) : (
          <div className="flex h-full items-center justify-center rounded-md border border-dashed border-border text-xs text-muted-foreground">
            Run output appears here.
          </div>
        )}
      </div>
    </div>
  );
}

// ─── Ledger row ────────────────────────────────────────────────────────

function LedgerRow({
  entry,
  onRunSkill,
  onRemove,
}: {
  entry: QueueEntry;
  onRunSkill: (entry: QueueEntry, req: SkillRequest, title: string) => void;
  onRemove: (entry: QueueEntry) => void;
}): React.JSX.Element {
  const action = inferAction(entry);

  const dispatchAction = (): void => {
    if (!action) return;
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
          <span className="truncate text-[12px] font-medium text-foreground/90" title={entry.title}>
            {entry.title}
          </span>
          <OriginTag origin={entry.origin} />
          {entry.lastValidated && (
            <span className="font-mono text-[10px] text-muted-foreground" title={`Last validated ${entry.lastValidated}`}>
              {entry.lastValidated}
              {entry.daysSinceValidated !== undefined && (
                <span className={cn('ml-1', entry.daysSinceValidated > 90 ? 'text-warning' : '')}>
                  ({entry.daysSinceValidated}d)
                </span>
              )}
            </span>
          )}
        </div>
        {entry.path && (
          <div className="truncate font-mono text-[10px] text-muted-foreground" title={entry.path}>
            {entry.path}
          </div>
        )}
        {entry.description && (
          <div className="mt-0.5 line-clamp-2 text-[11px] text-muted-foreground/80">
            {entry.description}
          </div>
        )}
      </div>
      {action && (
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
      )}
    </li>
  );
}

// ─── Status pill ───────────────────────────────────────────────────────

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

// ─── Filter ────────────────────────────────────────────────────────────

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
    tooltip: 'Article has confidence:high + recent last_validated — can be removed from queue',
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
