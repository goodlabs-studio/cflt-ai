import type React from 'react';
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeHighlight from 'rehype-highlight';
import {
  GitPullRequest,
  Send,
  Square,
  Package,
  AlertTriangle,
} from 'lucide-react';
import {
  GATE_NAMES,
  type GateName,
  type PlanMeta,
} from '@shared/types';
import { runSkill } from '@/lib/skill';
import { parsePlan } from '@/lib/plan-parse';
import { useNav } from '@/store/nav';
import { GateChain } from '@/components/plan/GateChain';
import { cn } from '@/lib/utils';

interface Status {
  kind: 'idle' | 'running' | 'complete' | 'error' | 'cancelled';
  message?: string;
}

export function PlanPage(): React.JSX.Element {
  const [request, setRequest] = useState('');
  const [overlay, setOverlay] = useState('');
  const [overlays, setOverlays] = useState<string[]>([]);
  const [bypass, setBypass] = useState<Set<GateName>>(new Set());
  const [status, setStatus] = useState<Status>({ kind: 'idle' });
  const [response, setResponse] = useState('');
  const [plans, setPlans] = useState<PlanMeta[]>([]);
  const cancelRef = useRef<(() => void) | null>(null);
  const planSeed = useNav((s) => s.planSeed);
  const setPlanSeed = useNav((s) => s.setPlanSeed);

  const parsed = useMemo(() => parsePlan(response), [response]);

  // Consume a one-shot deep-link seed from the Wiki "Plan this" action.
  useEffect(() => {
    if (planSeed) {
      setRequest(planSeed);
      setPlanSeed(null);
    }
  }, [planSeed, setPlanSeed]);

  useEffect(() => {
    let mounted = true;
    window.cflt.fs
      .listOverlays()
      .then((o) => mounted && setOverlays(o))
      .catch(() => {});
    const refresh = (): void => {
      window.cflt.fs.listPlans().then((p) => {
        if (!mounted) return;
        setPlans(p.slice(0, 30));
      });
    };
    refresh();
    const dispose = window.cflt.fs.watch(['outputs/plans/*.md'], refresh);
    return () => {
      mounted = false;
      dispose();
    };
  }, []);

  const submit = useCallback(async () => {
    const r = request.trim();
    if (!r || status.kind === 'running') return;
    setStatus({ kind: 'running' });
    setResponse('');

    const handle = runSkill({
      kind: 'dsp:plan',
      request: r,
      ...(overlay ? { overlay } : {}),
      ...(bypass.size > 0 ? { gateBypass: [...bypass] } : {}),
    });
    cancelRef.current = handle.cancel;

    let buffer = '';
    try {
      for await (const ev of handle.events) {
        switch (ev.type) {
          case 'assistant_text':
            buffer += ev.text;
            setResponse(buffer);
            break;
          case 'error':
            setStatus({ kind: 'error', message: ev.message });
            break;
          case 'result':
            cancelRef.current = null;
            if (!ev.result.success) {
              setStatus({
                kind: 'error',
                message: ev.result.text || 'Skill returned non-success',
              });
            } else {
              setStatus({ kind: 'complete' });
            }
            break;
        }
      }
    } catch (err) {
      setStatus({
        kind: 'error',
        message: err instanceof Error ? err.message : String(err),
      });
    }
  }, [request, overlay, bypass, status.kind]);

  const cancel = useCallback(() => {
    cancelRef.current?.();
    setStatus({ kind: 'cancelled' });
  }, []);

  const toggleBypass = useCallback((g: GateName) => {
    setBypass((cur) => {
      const next = new Set(cur);
      if (next.has(g)) next.delete(g);
      else next.add(g);
      return next;
    });
  }, []);

  const isRunning = status.kind === 'running';

  return (
    <div className="grid h-full grid-cols-[20rem_minmax(0,1fr)] gap-4 overflow-hidden p-4">
      <aside className="flex min-h-0 flex-col gap-3 overflow-auto">
        <RequestComposer
          request={request}
          setRequest={setRequest}
          submit={submit}
          isRunning={isRunning}
          onCancel={cancel}
        />

        <fieldset className="space-y-2 rounded-md border border-border bg-muted/20 p-3 text-[11px]">
          <legend className="px-1 text-[10px] uppercase tracking-wider text-muted-foreground/70">
            options
          </legend>
          <label className="flex items-center justify-between gap-2">
            <span className="text-muted-foreground">overlay:</span>
            <select
              value={overlay}
              onChange={(e) => setOverlay(e.target.value)}
              disabled={isRunning}
              className="flex-1 rounded bg-muted/60 px-1.5 py-0.5 text-foreground outline-none disabled:opacity-40"
            >
              <option value="">(base)</option>
              {overlays.map((o) => (
                <option key={o} value={o}>
                  {o}
                </option>
              ))}
            </select>
          </label>
          <BypassControl
            bypass={bypass}
            toggle={toggleBypass}
            disabled={isRunning}
          />
        </fieldset>

        <PastPlansRail plans={plans} />
      </aside>

      <div className="flex min-h-0 flex-col gap-3 overflow-hidden">
        <section className="rounded-md border border-border bg-muted/15 p-3">
          <div className="mb-2 flex items-center gap-1.5">
            <GitPullRequest className="h-3.5 w-3.5 text-cflt-blue" />
            <h3 className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
              4-gate validation chain
            </h3>
            {parsed.gatesComplete && (
              <span className="ml-auto rounded bg-success/15 px-1.5 py-0.5 font-mono text-[10px] text-success">
                complete
              </span>
            )}
          </div>
          <GateChain gates={parsed.gates} />
        </section>

        {parsed.artifact && (
          <ArtifactCard artifact={parsed.artifact} />
        )}

        {status.kind === 'error' && status.message && (
          <div className="rounded border border-danger/40 bg-danger/10 p-3 text-xs text-danger">
            {status.message}
          </div>
        )}

        <section className="flex min-h-0 flex-1 flex-col overflow-hidden rounded-md border border-border bg-background">
          <header className="border-b border-border bg-muted/20 px-3 py-1.5 text-[10px] font-medium uppercase tracking-wider text-muted-foreground/70">
            plan output
          </header>
          <div className="min-h-0 flex-1 overflow-auto px-6 py-4">
            {response ? (
              <div className="wiki-prose">
                <ReactMarkdown
                  remarkPlugins={[remarkGfm]}
                  rehypePlugins={[rehypeHighlight]}
                >
                  {response}
                </ReactMarkdown>
              </div>
            ) : (
              <div className="flex h-full items-center justify-center text-sm text-muted-foreground">
                {isRunning
                  ? 'streaming /dsp:plan response…'
                  : 'Type a request on the left, then run /dsp:plan.'}
              </div>
            )}
          </div>
        </section>
      </div>
    </div>
  );
}

function RequestComposer({
  request,
  setRequest,
  submit,
  isRunning,
  onCancel,
}: {
  request: string;
  setRequest: (s: string) => void;
  submit: () => void;
  isRunning: boolean;
  onCancel: () => void;
}): React.JSX.Element {
  return (
    <div className="rounded-md border border-border bg-muted/20 p-3">
      <textarea
        value={request}
        onChange={(e) => setRequest(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) submit();
        }}
        placeholder='e.g. "Create a compacted topic for payments.transaction.completed"'
        className="min-h-[5rem] w-full resize-none bg-transparent text-sm leading-relaxed outline-none placeholder:text-muted-foreground/60"
      />
      <div className="mt-2 flex items-center justify-end gap-1.5">
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
            disabled={!request.trim()}
            className="flex items-center gap-1 rounded bg-cflt-blue px-2.5 py-1 text-[11px] uppercase tracking-wide text-cflt-paper hover:opacity-90 disabled:opacity-40"
          >
            <Send className="h-3 w-3" />
            run /dsp:plan
          </button>
        )}
      </div>
    </div>
  );
}

function BypassControl({
  bypass,
  toggle,
  disabled,
}: {
  bypass: Set<GateName>;
  toggle: (g: GateName) => void;
  disabled: boolean;
}): React.JSX.Element {
  const has = bypass.size > 0;
  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between">
        <span className="text-muted-foreground">gate bypass:</span>
        {has && (
          <span className="flex items-center gap-1 text-[10px] text-warning">
            <AlertTriangle className="h-3 w-3" />
            dev mode
          </span>
        )}
      </div>
      <div className="flex flex-wrap gap-1">
        {GATE_NAMES.map((g) => {
          const active = bypass.has(g);
          return (
            <button
              key={g}
              type="button"
              disabled={disabled}
              onClick={() => toggle(g)}
              className={cn(
                'rounded px-1.5 py-0.5 font-mono text-[10px] transition-colors',
                active
                  ? 'bg-warning/20 text-warning'
                  : 'bg-muted/60 text-muted-foreground hover:text-foreground',
                disabled ? 'cursor-not-allowed opacity-40' : '',
              )}
              title={active ? `bypassing ${g}` : `click to bypass ${g}`}
            >
              {g}
            </button>
          );
        })}
      </div>
    </div>
  );
}

function ArtifactCard({
  artifact,
}: {
  artifact: NonNullable<ReturnType<typeof parsePlan>['artifact']>;
}): React.JSX.Element {
  return (
    <section className="rounded-md border border-cflt-blue/30 bg-cflt-blue/5 p-3">
      <div className="mb-1 flex items-center gap-1.5">
        <Package className="h-3.5 w-3.5 text-cflt-blue" />
        <h3 className="text-[11px] font-semibold uppercase tracking-wider text-cflt-blue">
          Selected Artifact
        </h3>
      </div>
      <div className="space-y-0.5 text-[12px]">
        <div className="flex gap-2">
          <span className="w-16 shrink-0 font-mono text-[10px] uppercase tracking-wider text-muted-foreground/70">
            id
          </span>
          <span className="font-mono text-foreground">{artifact.id}</span>
        </div>
        {artifact.path && (
          <div className="flex gap-2">
            <span className="w-16 shrink-0 font-mono text-[10px] uppercase tracking-wider text-muted-foreground/70">
              path
            </span>
            <span className="font-mono text-foreground/80">{artifact.path}</span>
          </div>
        )}
        {artifact.description && (
          <div className="flex gap-2">
            <span className="w-16 shrink-0 font-mono text-[10px] uppercase tracking-wider text-muted-foreground/70">
              desc
            </span>
            <span className="text-foreground/80">{artifact.description}</span>
          </div>
        )}
      </div>
    </section>
  );
}

function PastPlansRail({
  plans,
}: {
  plans: PlanMeta[];
}): React.JSX.Element {
  return (
    <aside className="flex min-h-0 flex-1 flex-col rounded-md border border-border bg-muted/10">
      <header className="border-b border-border px-3 py-2 text-[10px] font-medium uppercase tracking-wider text-muted-foreground/70">
        Past plans ({plans.length})
      </header>
      <ul className="flex-1 divide-y divide-border overflow-auto">
        {plans.length === 0 && (
          <li className="px-3 py-4 text-xs text-muted-foreground/60">
            No plans yet. Plans go to outputs/plans/.
          </li>
        )}
        {plans.map((p) => (
          <li key={p.slug} className="px-3 py-2 text-[11px]">
            <div className="font-mono text-[10px] text-muted-foreground">
              {p.date ?? '—'}
            </div>
            <div className="break-words text-foreground">{p.slug}</div>
          </li>
        ))}
      </ul>
    </aside>
  );
}
