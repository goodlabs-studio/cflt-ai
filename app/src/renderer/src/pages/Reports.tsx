import type React from 'react';
import { useCallback, useEffect, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeHighlight from 'rehype-highlight';
import type { ReportMeta } from '@shared/types';
import { useBadges } from '@/store/badges';
import { cn } from '@/lib/utils';

export function ReportsPage(): React.JSX.Element {
  const [reports, setReports] = useState<ReportMeta[]>([]);
  const [activeSlug, setActiveSlug] = useState<string | null>(null);
  const [body, setBody] = useState<string>('');
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(() => {
    window.cflt.fs
      .listReports()
      .then((rs) => {
        setReports(rs);
        if (!activeSlug && rs.length > 0) setActiveSlug(rs[0].slug);
      })
      .catch((e: Error) => setError(e.message));
  }, [activeSlug]);

  // Initial load + filesystem watch on outputs/reports/
  useEffect(() => {
    refresh();
    const dispose = window.cflt.fs.watch(['outputs/reports/*.md'], () => {
      refresh();
    });
    return dispose;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Drain the unread badge: mark all current reports seen while this page is
  // open, and again whenever new reports land here (inbox-on-screen behavior).
  const reportSlugs = useBadges((s) => s.reportSlugs);
  const markReportsRead = useBadges((s) => s.markReportsRead);
  useEffect(() => {
    markReportsRead();
  }, [reportSlugs, markReportsRead]);

  // Load active report body
  useEffect(() => {
    if (!activeSlug) {
      setBody('');
      return;
    }
    let mounted = true;
    window.cflt.fs
      .readReport(activeSlug)
      .then((b) => mounted && setBody(b))
      .catch((e: Error) => mounted && setError(e.message));
    return () => {
      mounted = false;
    };
  }, [activeSlug]);

  return (
    <div className="grid h-full grid-cols-[20rem_minmax(0,1fr)] overflow-hidden">
      <ReportList
        reports={reports}
        activeSlug={activeSlug}
        onSelect={setActiveSlug}
      />
      <div className="min-w-0 overflow-hidden">
        {error && (
          <div className="m-6 rounded border border-danger/40 bg-danger/10 p-4 text-sm text-danger">
            {error}
          </div>
        )}
        {!error && activeSlug && body && (
          <div className="h-full overflow-auto px-8 py-6">
            <header className="mb-4 border-b border-border pb-3">
              <div className="font-mono text-[11px] text-muted-foreground">
                outputs/reports/{activeSlug}.md
              </div>
            </header>
            <div className="wiki-prose">
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                rehypePlugins={[rehypeHighlight]}
              >
                {body}
              </ReactMarkdown>
            </div>
          </div>
        )}
        {!error && reports.length === 0 && (
          <div className="flex h-full items-center justify-center text-sm text-muted-foreground">
            No reports yet. Run /ask --mode report or /review to generate one.
          </div>
        )}
      </div>
    </div>
  );
}

function ReportList({
  reports,
  activeSlug,
  onSelect,
}: {
  reports: ReportMeta[];
  activeSlug: string | null;
  onSelect: (slug: string) => void;
}): React.JSX.Element {
  return (
    <aside className="overflow-auto border-r border-border bg-muted/10">
      <ul className="divide-y divide-border">
        {reports.map((r) => {
          const isActive = r.slug === activeSlug;
          return (
            <li key={r.slug}>
              <button
                type="button"
                onClick={() => onSelect(r.slug)}
                className={cn(
                  'flex w-full flex-col gap-1.5 px-3 py-2.5 text-left transition-colors',
                  isActive
                    ? 'bg-cflt-blue/10'
                    : 'hover:bg-muted/40',
                )}
              >
                <div className="flex items-center justify-between gap-2">
                  <span className="font-mono text-[10px] text-muted-foreground">
                    {r.date ?? '—'}
                  </span>
                  {r.sourceSkill && (
                    <span className="rounded bg-muted px-1.5 py-0.5 font-mono text-[10px] text-muted-foreground">
                      {r.sourceSkill}
                    </span>
                  )}
                </div>
                <div className="break-words text-[13px] text-foreground">
                  {r.slug}
                </div>
                <ClaimBadges meta={r} />
              </button>
            </li>
          );
        })}
      </ul>
    </aside>
  );
}

function ClaimBadges({ meta }: { meta: ReportMeta }): React.JSX.Element {
  const has =
    meta.claimsChecked !== undefined ||
    meta.claimsCorrected !== undefined ||
    meta.claimsUnverifiable !== undefined;
  if (!has) {
    return (
      <div className="text-[10px] text-muted-foreground/60">claims: —</div>
    );
  }
  return (
    <div className="flex items-center gap-1.5 text-[10px]">
      <Badge label="checked" value={meta.claimsChecked} tone="muted" />
      <Badge label="corrected" value={meta.claimsCorrected} tone="warning" />
      <Badge label="unverifiable" value={meta.claimsUnverifiable} tone="danger" />
    </div>
  );
}

function Badge({
  label,
  value,
  tone,
}: {
  label: string;
  value: number | undefined;
  tone: 'muted' | 'warning' | 'danger';
}): React.JSX.Element {
  if (value === undefined || value === 0) {
    return (
      <span className="rounded bg-muted/60 px-1.5 py-0.5 font-mono text-muted-foreground/60">
        {label} 0
      </span>
    );
  }
  const cls =
    tone === 'warning'
      ? 'bg-warning/15 text-warning'
      : tone === 'danger'
        ? 'bg-danger/15 text-danger'
        : 'bg-muted text-muted-foreground';
  return (
    <span className={cn('rounded px-1.5 py-0.5 font-mono', cls)}>
      {label} {value}
    </span>
  );
}
