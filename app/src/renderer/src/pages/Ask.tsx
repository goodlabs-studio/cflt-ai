import type React from 'react';
import { useCallback, useEffect, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeHighlight from 'rehype-highlight';
import { Loader2, Send, Square, X } from 'lucide-react';
import type { AskMode, ClaudeRoute, ReportMeta } from '@shared/types';
import { runSkill } from '@/lib/skill';
import { useAsk, type AskStatus } from '@/store/ask';
import { cn } from '@/lib/utils';
import { RouteBadge } from '@/components/ask/RouteBadge';

const MODES: { value: AskMode; label: string; hint: string }[] = [
  {
    value: 'ephemeral',
    label: 'Ephemeral',
    hint: 'no files written; in-chat answer',
  },
  {
    value: 'report',
    label: 'Report',
    hint: 'writes outputs/reports/<slug>.md',
  },
  {
    value: 'reconsolidate',
    label: 'Reconsolidate',
    hint: 'report + wiki updates + auto-stubs',
  },
];

// Placeholder shifts with the mode so the user knows what submitting will do.
const MODE_PLACEHOLDERS: Record<AskMode, string> = {
  ephemeral: 'Ask a Confluent / Kafka / Flink question. ⌘↵ to submit.',
  report:
    'Ask a question worth keeping — the validated answer is saved as a report in outputs/reports/. ⌘↵ to submit.',
  reconsolidate:
    'Ask something that should improve the wiki — writes a report and folds new findings back into canon (updates articles, stubs gaps). ⌘↵ to submit.',
};

const ROUTE_OPTIONS: { value: ClaudeRoute | 'auto'; label: string }[] = [
  { value: 'auto', label: 'auto' },
  { value: 'wiki', label: 'wiki-only' },
  { value: 'mcp', label: 'wiki + MCP' },
  { value: 'deep', label: 'deep' },
];

export function AskPage(): React.JSX.Element {
  const [query, setQuery] = useState('');
  const {
    status,
    mode,
    forceRoute,
    route,
    responseText,
    errorMessage,
    result,
    setMode,
    setForceRoute,
    start,
    appendText,
    setRoute,
    finish,
    fail,
    cancel,
    reset,
  } = useAsk();

  const submit = useCallback(async () => {
    const q = query.trim();
    if (!q || status === 'classifying' || status === 'streaming') return;

    const handle = runSkill({
      kind: 'ask',
      query: q,
      mode,
      ...(forceRoute !== 'auto' ? { forceRoute } : {}),
    });
    start(handle);

    try {
      for await (const ev of handle.events) {
        switch (ev.type) {
          case 'assistant_text':
            appendText(ev.text);
            break;
          case 'route':
            setRoute(ev.route);
            break;
          case 'error':
            fail(ev.message);
            break;
          case 'result':
            if (!ev.result.success) {
              fail(ev.result.text || 'Skill returned non-success');
            } else {
              finish(ev.result);
            }
            break;
          // init/system/tool_use/tool_result/rate_limit/raw — ignored on Ask
        }
      }
    } catch (err) {
      fail(err instanceof Error ? err.message : String(err));
    }
  }, [query, mode, forceRoute, status, start, appendText, setRoute, finish, fail]);

  const isRunning = status === 'classifying' || status === 'streaming';

  return (
    <div className="grid h-full grid-cols-[minmax(0,1fr)_18rem] gap-4 overflow-hidden p-6">
      <div className="flex min-h-0 flex-col gap-4">
        <QueryComposer
          query={query}
          setQuery={setQuery}
          mode={mode}
          setMode={setMode}
          forceRoute={forceRoute}
          setForceRoute={setForceRoute}
          submit={submit}
          isRunning={isRunning}
          onCancel={cancel}
        />
        <div className="flex items-center gap-2">
          <RouteBadge status={status} route={route} />
          {result && (
            <span className="font-mono text-[11px] text-muted-foreground">
              {result.durationMs}ms · ${result.costUsd.toFixed(4)} ·{' '}
              {result.inputTokens.toLocaleString()}↦{' '}
              {result.outputTokens.toLocaleString()} tokens
            </span>
          )}
        </div>
        {errorMessage && (
          <div className="rounded border border-danger/40 bg-danger/10 p-3 text-xs text-danger">
            {errorMessage}
          </div>
        )}
        <ResponsePane text={responseText} status={status} onReset={reset} />
      </div>
      <PastAsksRail />
    </div>
  );
}

function QueryComposer({
  query,
  setQuery,
  mode,
  setMode,
  forceRoute,
  setForceRoute,
  submit,
  isRunning,
  onCancel,
}: {
  query: string;
  setQuery: (q: string) => void;
  mode: AskMode;
  setMode: (m: AskMode) => void;
  forceRoute: ClaudeRoute | 'auto';
  setForceRoute: (r: ClaudeRoute | 'auto') => void;
  submit: () => void;
  isRunning: boolean;
  onCancel: () => void;
}): React.JSX.Element {
  return (
    <div className="rounded-md border border-border bg-muted/20 p-3">
      <textarea
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) submit();
        }}
        placeholder={MODE_PLACEHOLDERS[mode]}
        className="min-h-[5rem] w-full resize-none bg-transparent text-sm leading-relaxed outline-none placeholder:text-muted-foreground/60"
      />
      <div className="mt-2 flex items-center justify-between gap-2">
        <div className="flex items-center gap-2 text-[11px]">
          <ModeSelect mode={mode} setMode={setMode} disabled={isRunning} />
          <ForceRouteSelect
            forceRoute={forceRoute}
            setForceRoute={setForceRoute}
            disabled={isRunning}
          />
        </div>
        <div className="flex items-center gap-1.5">
          {isRunning ? (
            <button
              type="button"
              onClick={onCancel}
              className="flex items-center gap-1 rounded bg-danger/15 px-2.5 py-1 text-[11px] uppercase tracking-wide text-danger hover:bg-danger/25"
            >
              <Square className="h-3 w-3" />
              cancel
            </button>
          ) : (
            <button
              type="button"
              onClick={submit}
              disabled={!query.trim()}
              className="flex items-center gap-1 rounded bg-cflt-blue px-2.5 py-1 text-[11px] uppercase tracking-wide text-cflt-paper hover:opacity-90 disabled:opacity-40"
            >
              <Send className="h-3 w-3" />
              ask
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

function ModeSelect({
  mode,
  setMode,
  disabled,
}: {
  mode: AskMode;
  setMode: (m: AskMode) => void;
  disabled: boolean;
}): React.JSX.Element {
  return (
    <div className="flex items-center gap-1 rounded bg-muted/60 p-0.5">
      {MODES.map((m) => (
        <button
          key={m.value}
          type="button"
          disabled={disabled}
          title={m.hint}
          onClick={() => setMode(m.value)}
          className={cn(
            'rounded px-2 py-0.5 uppercase tracking-wide transition-colors',
            mode === m.value
              ? 'bg-background text-foreground'
              : 'text-muted-foreground hover:text-foreground',
            disabled ? 'cursor-not-allowed opacity-40' : '',
          )}
        >
          {m.label}
        </button>
      ))}
    </div>
  );
}

function ForceRouteSelect({
  forceRoute,
  setForceRoute,
  disabled,
}: {
  forceRoute: ClaudeRoute | 'auto';
  setForceRoute: (r: ClaudeRoute | 'auto') => void;
  disabled: boolean;
}): React.JSX.Element {
  return (
    <label className="flex items-center gap-1 text-muted-foreground">
      <span>route:</span>
      <select
        disabled={disabled}
        value={forceRoute}
        onChange={(e) => setForceRoute(e.target.value as ClaudeRoute | 'auto')}
        className="rounded bg-muted/60 px-1.5 py-0.5 text-foreground outline-none disabled:opacity-40"
      >
        {ROUTE_OPTIONS.map((o) => (
          <option key={o.value} value={o.value}>
            {o.label}
          </option>
        ))}
      </select>
    </label>
  );
}

function ResponsePane({
  text,
  status,
  onReset,
}: {
  text: string;
  status: AskStatus;
  onReset: () => void;
}): React.JSX.Element {
  if (status === 'idle' && !text) {
    return (
      <div className="flex flex-1 items-center justify-center rounded-md border border-dashed border-border text-xs text-muted-foreground">
        Submit a question to start.
      </div>
    );
  }
  return (
    <div className="relative flex-1 overflow-hidden rounded-md border border-border bg-background">
      {(status === 'complete' || status === 'cancelled' || status === 'error') && (
        <button
          type="button"
          onClick={onReset}
          className="absolute right-2 top-2 z-10 rounded p-1 text-muted-foreground hover:bg-muted hover:text-foreground"
          title="Clear response"
        >
          <X className="h-3.5 w-3.5" />
        </button>
      )}
      <div className="h-full overflow-auto px-6 py-5">
        <div className="wiki-prose">
          {text ? (
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              rehypePlugins={[rehypeHighlight]}
            >
              {text}
            </ReactMarkdown>
          ) : (
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              <Loader2 className="h-3 w-3 animate-spin" />
              waiting for first token…
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function PastAsksRail(): React.JSX.Element {
  const [reports, setReports] = useState<ReportMeta[]>([]);

  useEffect(() => {
    let mounted = true;
    const refresh = (): void => {
      window.cflt.fs.listReports().then((rs) => {
        if (!mounted) return;
        setReports(rs.filter((r) => r.sourceSkill === '/ask').slice(0, 30));
      });
    };
    refresh();
    const dispose = window.cflt.fs.watch(['outputs/reports/*.md'], refresh);
    return () => {
      mounted = false;
      dispose();
    };
  }, []);

  return (
    <aside className="flex h-full min-h-0 flex-col rounded-md border border-border bg-muted/10">
      <header className="border-b border-border px-3 py-2 text-[10px] font-medium uppercase tracking-wider text-muted-foreground/70">
        Past asks ({reports.length})
      </header>
      <ul className="flex-1 divide-y divide-border overflow-auto">
        {reports.length === 0 && (
          <li className="px-3 py-4 text-xs text-muted-foreground/60">
            No past /ask reports yet. Reports written via mode=report or
            reconsolidate appear here.
          </li>
        )}
        {reports.map((r) => (
          <li key={r.slug} className="px-3 py-2 text-[11px]">
            <div className="font-mono text-[10px] text-muted-foreground">
              {r.date ?? '—'}
            </div>
            <div className="break-words text-foreground">{r.slug}</div>
          </li>
        ))}
      </ul>
    </aside>
  );
}
