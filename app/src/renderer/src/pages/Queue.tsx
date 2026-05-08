import type React from 'react';
import { useCallback, useEffect, useRef, useState } from 'react';
import { Play, RefreshCw, ListChecks } from 'lucide-react';
import type { QueueSection, SkillRequest } from '@shared/types';
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

const STUB_LINK_RE = /\[([^\]]+)\]\(([^)]+\.md)\)/;

export function QueuePage(): React.JSX.Element {
  const [sections, setSections] = useState<QueueSection[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [activePanel, setActivePanel] = useState<RunPanelState | null>(null);
  const cancelRef = useRef<(() => void) | null>(null);

  const refresh = useCallback(() => {
    window.cflt.fs
      .readQueue()
      .then((s) => setSections(s))
      .catch((e: Error) => setError(e.message));
  }, []);

  useEffect(() => {
    refresh();
    const dispose = window.cflt.fs.watch(['wiki/_queue.md'], refresh);
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
      // Append per-line to make scrolling natural
      for (const piece of text.split('\n')) {
        if (piece) lines.push(piece);
      }
      appended = true;
      // Force re-render with same array reference doesn't work; clone
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
  }, [setPanel]);

  const runSkillCmd = useCallback(
    async (req: SkillRequest, title: string) => {
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
            return;
          }
        }
      }
    },
    [setPanel],
  );

  return (
    <div className="grid h-full grid-cols-[minmax(0,1fr)_22rem] gap-4 overflow-hidden p-4">
      <div className="flex min-h-0 flex-col gap-3">
        <header className="flex items-center justify-between rounded-md border border-border bg-muted/20 px-3 py-2">
          <div className="flex items-center gap-2">
            <ListChecks className="h-4 w-4 text-cflt-blue" />
            <h1 className="text-sm font-semibold tracking-tight text-foreground">
              Wiki Queue
            </h1>
            <span className="text-[11px] text-muted-foreground">
              {sections.reduce((n, s) => n + s.entries.length, 0)} items across{' '}
              {sections.length} sections
            </span>
          </div>
          <div className="flex items-center gap-1.5">
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
          <div className="rounded border border-danger/40 bg-danger/10 p-3 text-xs text-danger">
            {error}
          </div>
        )}
        <div className="grid min-h-0 flex-1 grid-cols-2 gap-3 overflow-auto">
          {sections.length === 0 && !error && (
            <div className="col-span-2 flex items-center justify-center text-sm text-muted-foreground">
              wiki/_queue.md is empty.
            </div>
          )}
          {sections.map((section) => (
            <SectionColumn
              key={section.heading}
              section={section}
              onRun={runSkillCmd}
            />
          ))}
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

function SectionColumn({
  section,
  onRun,
}: {
  section: QueueSection;
  onRun: (req: SkillRequest, title: string) => void;
}): React.JSX.Element {
  const verb = inferAction(section.heading);

  return (
    <section className="flex min-h-0 flex-col rounded-md border border-border bg-muted/10">
      <header className="flex items-center justify-between border-b border-border px-3 py-2 text-[11px]">
        <span className="uppercase tracking-wider text-muted-foreground/70">
          {section.heading}
        </span>
        <span className="font-mono text-[10px] text-muted-foreground">
          {section.entries.length}
        </span>
      </header>
      <ul className="flex-1 space-y-1 overflow-auto p-2">
        {section.entries.length === 0 && (
          <li className="px-2 py-3 text-center text-[11px] text-muted-foreground/60">
            empty
          </li>
        )}
        {section.entries.map((entry, idx) => (
          <li
            key={idx}
            className="group rounded border border-transparent bg-background/40 p-2 text-[12px] hover:border-border"
          >
            <div className="break-words text-foreground/90">{entry.trim()}</div>
            {verb && (
              <div className="mt-1.5 flex items-center justify-end gap-1 opacity-0 transition-opacity group-hover:opacity-100">
                <button
                  type="button"
                  onClick={() => {
                    const args = extractEntryRef(entry);
                    onRun(
                      verb === '/wiki:ingest'
                        ? { kind: 'wiki:ingest', args }
                        : { kind: 'wiki:validate', args },
                      `${verb}${args ? ` ${args}` : ''}`,
                    );
                  }}
                  className={cn(
                    'flex items-center gap-1 rounded px-1.5 py-0.5 text-[10px] uppercase tracking-wide',
                    verb === '/wiki:ingest'
                      ? 'bg-warning/15 text-warning hover:bg-warning/25'
                      : 'bg-cflt-blue/15 text-cflt-blue hover:bg-cflt-blue/25',
                  )}
                >
                  <Play className="h-2.5 w-2.5" />
                  {verb}
                </button>
              </div>
            )}
          </li>
        ))}
      </ul>
    </section>
  );
}

/**
 * Map the section heading to the skill that resolves entries in it.
 *   "Stubs to Create"          → /wiki:ingest
 *   "Articles to Expand"       → /wiki:ingest
 *   "Candidate Articles"       → /wiki:ingest
 *   "Auto-Stubs"               → /wiki:ingest
 *   "Unverified Claims to Resolve" → /wiki:validate
 *   "Lint Findings"            → /wiki:lint (panel-level button only)
 */
function inferAction(heading: string): '/wiki:ingest' | '/wiki:validate' | null {
  const h = heading.toLowerCase();
  if (h.includes('lint findings')) return null;
  if (h.includes('unverified') || h.includes('verify') || h.includes('drift'))
    return '/wiki:validate';
  if (h.includes('stub') || h.includes('expand') || h.includes('candidate') || h.includes('ingest'))
    return '/wiki:ingest';
  return '/wiki:ingest';
}

function extractEntryRef(entry: string): string {
  // Prefer markdown link target if present
  const m = STUB_LINK_RE.exec(entry);
  if (m) return m[2];
  // Otherwise pass the raw (trimmed) line so the skill can parse it
  return entry.replace(/^[-*]\s*/, '').trim();
}
