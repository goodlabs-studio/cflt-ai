import type React from 'react';
import { useEffect, useRef } from 'react';
import { Loader2, Square, X, CheckCircle2, AlertCircle } from 'lucide-react';
import { cn } from '@/lib/utils';

export type RunPanelStatus = 'idle' | 'running' | 'success' | 'error' | 'cancelled';

interface Props {
  title: string;
  status: RunPanelStatus;
  /** Pre-formatted lines of output (stdout + stderr interleaved). */
  lines: string[];
  /** Optional small badge after the title (e.g., exit code). */
  meta?: string;
  onCancel?: () => void;
  onClose?: () => void;
}

/**
 * Reusable terminal-style streaming output panel. Used by the Queue page
 * for `wiki:lint` (tool fast-path) and `/wiki:ingest` / `/wiki:validate`
 * (skill subprocess). Auto-scrolls to bottom while running.
 */
export function RunPanel({
  title,
  status,
  lines,
  meta,
  onCancel,
  onClose,
}: Props): React.JSX.Element {
  const bodyRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (status === 'running' && bodyRef.current) {
      bodyRef.current.scrollTop = bodyRef.current.scrollHeight;
    }
  }, [lines, status]);

  return (
    <div className="flex h-full min-h-0 flex-col rounded-md border border-border bg-cflt-ink/60">
      <header className="flex items-center justify-between gap-2 border-b border-border px-3 py-2 text-[11px]">
        <div className="flex items-center gap-2">
          <StatusIcon status={status} />
          <span className="font-mono text-foreground">{title}</span>
          {meta && (
            <span className="rounded bg-muted px-1.5 py-0.5 font-mono text-[10px] text-muted-foreground">
              {meta}
            </span>
          )}
        </div>
        <div className="flex items-center gap-1">
          {status === 'running' && onCancel && (
            <button
              type="button"
              onClick={onCancel}
              className="flex items-center gap-1 rounded bg-danger/15 px-1.5 py-0.5 text-[10px] uppercase tracking-wide text-danger hover:bg-danger/25"
            >
              <Square className="h-2.5 w-2.5" />
              cancel
            </button>
          )}
          {onClose && status !== 'running' && (
            <button
              type="button"
              onClick={onClose}
              className="rounded p-0.5 text-muted-foreground hover:bg-muted hover:text-foreground"
              title="Close"
            >
              <X className="h-3 w-3" />
            </button>
          )}
        </div>
      </header>
      <div
        ref={bodyRef}
        className="min-h-0 flex-1 overflow-auto p-3 font-mono text-[11px] leading-relaxed text-muted-foreground"
      >
        {lines.length === 0 ? (
          <div className="text-muted-foreground/60">no output yet…</div>
        ) : (
          lines.map((l, i) => <div key={i} className="whitespace-pre-wrap">{l}</div>)
        )}
      </div>
    </div>
  );
}

function StatusIcon({ status }: { status: RunPanelStatus }): React.JSX.Element {
  switch (status) {
    case 'running':
      return <Loader2 className="h-3 w-3 animate-spin text-cflt-blue" />;
    case 'success':
      return <CheckCircle2 className="h-3 w-3 text-success" />;
    case 'error':
    case 'cancelled':
      return <AlertCircle className={cn('h-3 w-3', status === 'error' ? 'text-danger' : 'text-warning')} />;
    case 'idle':
    default:
      return <div className="h-3 w-3 rounded-full border border-muted-foreground/30" />;
  }
}
