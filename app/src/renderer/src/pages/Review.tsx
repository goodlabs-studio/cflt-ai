import type React from 'react';
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeHighlight from 'rehype-highlight';
import {
  Upload,
  X,
  FileText,
  Send,
  Square,
  ClipboardCheck,
  FolderOpen,
  FileDown,
} from 'lucide-react';
import type { ReportMeta } from '@shared/types';
import { runSkill } from '@/lib/skill';
import { parseReview } from '@/lib/review-parse';
import { ClaimTable } from '@/components/review/ClaimTable';
import { cn } from '@/lib/utils';

type OutputFormat = 'md' | 'docx' | 'both';

interface Status {
  kind: 'idle' | 'running' | 'complete' | 'error' | 'cancelled';
  message?: string;
}

export function ReviewPage(): React.JSX.Element {
  const [files, setFiles] = useState<string[]>([]);
  const [overlay, setOverlay] = useState<string>('');
  const [overlays, setOverlays] = useState<string[]>([]);
  const [output, setOutput] = useState<OutputFormat>('md');
  const [status, setStatus] = useState<Status>({ kind: 'idle' });
  const [response, setResponse] = useState('');
  const [reports, setReports] = useState<ReportMeta[]>([]);
  const [view, setView] = useState<'response' | 'claims'>('response');
  const [docxPath, setDocxPath] = useState<string | null>(null);
  const cancelRef = useRef<(() => void) | null>(null);

  const parsed = useMemo(() => parseReview(response), [response]);

  // Load overlays + past reviews
  useEffect(() => {
    let mounted = true;
    window.cflt.fs
      .listOverlays()
      .then((o) => mounted && setOverlays(o))
      .catch(() => {});
    const refresh = (): void => {
      window.cflt.fs.listReports().then((rs) => {
        if (!mounted) return;
        setReports(rs.filter((r) => r.sourceSkill === '/review').slice(0, 30));
      });
    };
    refresh();
    const dispose = window.cflt.fs.watch(['outputs/reports/*.md'], refresh);
    return () => {
      mounted = false;
      dispose();
    };
  }, []);

  const onDrop = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    const dropped: string[] = [];
    for (const f of Array.from(e.dataTransfer.files)) {
      // electron exposes the absolute path on File via legacy `path`
      const path =
        (f as File & { path?: string }).path ?? '';
      if (path) dropped.push(path);
    }
    if (dropped.length > 0) setFiles((cur) => [...cur, ...dropped]);
  }, []);

  const onBrowse = useCallback(async () => {
    const picked = await window.cflt.dialog.openReviewFiles();
    if (picked.length > 0) setFiles((cur) => [...cur, ...picked]);
  }, []);

  const removeFile = useCallback((idx: number) => {
    setFiles((cur) => cur.filter((_, i) => i !== idx));
  }, []);

  const submit = useCallback(async () => {
    if (files.length === 0 || status.kind === 'running') return;
    setStatus({ kind: 'running' });
    setResponse('');
    setView('response');
    setDocxPath(null);

    const handle = runSkill({
      kind: 'review',
      docPaths: files,
      output,
      ...(overlay ? { overlay } : {}),
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
              // Auto-flip to claim view if any claims were extracted
              setView((v) =>
                parsed.claims.length > 0 || /```yaml/.test(buffer) ? 'claims' : v,
              );
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
  }, [files, overlay, output, status.kind, parsed.claims.length]);

  const cancel = useCallback(() => {
    cancelRef.current?.();
    setStatus({ kind: 'cancelled' });
  }, []);

  const exportDocx = useCallback(async () => {
    // Find the most recent /review report; assume it was just written.
    const latest = reports.find((r) => r.sourceSkill === '/review');
    if (!latest) {
      setStatus({ kind: 'error', message: 'No /review report on disk to export.' });
      return;
    }
    try {
      const path = await window.cflt.tools.reviewToDocx(latest.path);
      setDocxPath(path);
    } catch (err) {
      setStatus({
        kind: 'error',
        message: err instanceof Error ? err.message : String(err),
      });
    }
  }, [reports]);

  const isRunning = status.kind === 'running';

  return (
    <div className="grid h-full grid-cols-[20rem_minmax(0,1fr)] gap-4 overflow-hidden p-4">
      <aside className="flex min-h-0 flex-col gap-3 overflow-auto">
        <DropZone files={files} onDrop={onDrop} onBrowse={onBrowse} onRemove={removeFile} />

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
              <option value="">(none)</option>
              {overlays.map((o) => (
                <option key={o} value={o}>
                  {o}
                </option>
              ))}
            </select>
          </label>
          <label className="flex items-center justify-between gap-2">
            <span className="text-muted-foreground">output:</span>
            <div className="flex items-center gap-1 rounded bg-muted/60 p-0.5">
              {(['md', 'docx', 'both'] as OutputFormat[]).map((f) => (
                <button
                  key={f}
                  type="button"
                  disabled={isRunning}
                  onClick={() => setOutput(f)}
                  className={cn(
                    'rounded px-2 py-0.5 uppercase tracking-wide transition-colors',
                    output === f
                      ? 'bg-background text-foreground'
                      : 'text-muted-foreground hover:text-foreground',
                    isRunning ? 'cursor-not-allowed opacity-40' : '',
                  )}
                >
                  {f}
                </button>
              ))}
            </div>
          </label>
        </fieldset>

        <div className="flex items-center gap-1.5">
          {isRunning ? (
            <button
              type="button"
              onClick={cancel}
              className="flex flex-1 items-center justify-center gap-1 rounded bg-danger/15 px-2.5 py-1.5 text-[11px] uppercase tracking-wide text-danger hover:bg-danger/25"
            >
              <Square className="h-3 w-3" />
              cancel
            </button>
          ) : (
            <button
              type="button"
              onClick={submit}
              disabled={files.length === 0}
              className="flex flex-1 items-center justify-center gap-1 rounded bg-cflt-blue px-2.5 py-1.5 text-[11px] uppercase tracking-wide text-cflt-paper hover:opacity-90 disabled:opacity-40"
            >
              <Send className="h-3 w-3" />
              run /review
            </button>
          )}
        </div>

        <PastReviewsRail reports={reports} />
      </aside>

      <div className="flex min-h-0 flex-col overflow-hidden rounded-md border border-border bg-background">
        <header className="flex items-center justify-between border-b border-border bg-muted/20 px-3 py-2">
          <ViewToggle view={view} onChange={setView} parsedHasClaims={parsed.claims.length > 0} />
          <div className="flex items-center gap-2">
            {status.kind === 'complete' && (
              <button
                type="button"
                onClick={exportDocx}
                className="flex items-center gap-1 rounded bg-cflt-blue/15 px-2.5 py-1 text-[11px] uppercase tracking-wide text-cflt-blue hover:bg-cflt-blue/25"
              >
                <FileDown className="h-3 w-3" />
                export docx
              </button>
            )}
            {docxPath && (
              <span className="font-mono text-[10px] text-muted-foreground">
                wrote {docxPath.split('/').slice(-1)[0]}
              </span>
            )}
          </div>
        </header>
        {status.kind === 'error' && status.message && (
          <div className="m-3 rounded border border-danger/40 bg-danger/10 p-3 text-xs text-danger">
            {status.message}
          </div>
        )}
        <div className="min-h-0 flex-1 overflow-auto px-6 py-4">
          {view === 'response' ? (
            response ? (
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
                {status.kind === 'running'
                  ? 'streaming /review response…'
                  : 'Drop or browse documents on the left, then run /review.'}
              </div>
            )
          ) : (
            <ClaimTable parsed={parsed} />
          )}
        </div>
      </div>
    </div>
  );
}

function DropZone({
  files,
  onDrop,
  onBrowse,
  onRemove,
}: {
  files: string[];
  onDrop: (e: React.DragEvent<HTMLDivElement>) => void;
  onBrowse: () => void;
  onRemove: (idx: number) => void;
}): React.JSX.Element {
  const [hot, setHot] = useState(false);
  return (
    <div
      onDragEnter={() => setHot(true)}
      onDragLeave={() => setHot(false)}
      onDragOver={(e) => {
        e.preventDefault();
        setHot(true);
      }}
      onDrop={(e) => {
        setHot(false);
        onDrop(e);
      }}
      className={cn(
        'rounded-md border-2 border-dashed p-3 transition-colors',
        hot
          ? 'border-cflt-blue bg-cflt-blue/10'
          : 'border-border bg-muted/10 hover:border-muted-foreground/40',
      )}
    >
      <div className="flex items-center justify-between">
        <span className="flex items-center gap-1.5 text-[11px] uppercase tracking-wider text-muted-foreground">
          <ClipboardCheck className="h-3.5 w-3.5" />
          documents
        </span>
        <button
          type="button"
          onClick={onBrowse}
          className="flex items-center gap-1 rounded px-1.5 py-0.5 text-[10px] uppercase tracking-wider text-muted-foreground hover:bg-muted hover:text-foreground"
        >
          <FolderOpen className="h-3 w-3" />
          browse
        </button>
      </div>
      {files.length === 0 ? (
        <div className="mt-3 flex flex-col items-center gap-1 px-2 py-4 text-center">
          <Upload className="h-5 w-5 text-muted-foreground/60" />
          <span className="text-[11px] text-muted-foreground/70">
            drop .md / .yaml here
          </span>
        </div>
      ) : (
        <ul className="mt-2 space-y-1">
          {files.map((f, i) => (
            <li
              key={`${f}-${i}`}
              className="flex items-center gap-1.5 rounded bg-background/60 px-2 py-1 text-[11px]"
            >
              <FileText className="h-3 w-3 shrink-0 text-cflt-blue" />
              <span
                className="flex-1 truncate font-mono text-foreground"
                title={f}
              >
                {f.split('/').slice(-1)[0]}
              </span>
              <button
                type="button"
                onClick={() => onRemove(i)}
                className="rounded p-0.5 text-muted-foreground hover:bg-muted hover:text-foreground"
              >
                <X className="h-3 w-3" />
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

function ViewToggle({
  view,
  onChange,
  parsedHasClaims,
}: {
  view: 'response' | 'claims';
  onChange: (v: 'response' | 'claims') => void;
  parsedHasClaims: boolean;
}): React.JSX.Element {
  return (
    <div className="flex items-center gap-1 rounded bg-muted/60 p-0.5 text-[11px]">
      <button
        type="button"
        onClick={() => onChange('response')}
        className={cn(
          'rounded px-2 py-0.5 uppercase tracking-wide',
          view === 'response'
            ? 'bg-background text-foreground'
            : 'text-muted-foreground hover:text-foreground',
        )}
      >
        response
      </button>
      <button
        type="button"
        onClick={() => onChange('claims')}
        disabled={!parsedHasClaims}
        className={cn(
          'rounded px-2 py-0.5 uppercase tracking-wide',
          view === 'claims'
            ? 'bg-background text-foreground'
            : 'text-muted-foreground hover:text-foreground',
          !parsedHasClaims ? 'cursor-not-allowed opacity-40' : '',
        )}
      >
        claims
      </button>
    </div>
  );
}

function PastReviewsRail({
  reports,
}: {
  reports: ReportMeta[];
}): React.JSX.Element {
  return (
    <aside className="flex min-h-0 flex-1 flex-col rounded-md border border-border bg-muted/10">
      <header className="border-b border-border px-3 py-2 text-[10px] font-medium uppercase tracking-wider text-muted-foreground/70">
        Past reviews ({reports.length})
      </header>
      <ul className="flex-1 divide-y divide-border overflow-auto">
        {reports.length === 0 && (
          <li className="px-3 py-4 text-xs text-muted-foreground/60">
            No /review reports yet.
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
