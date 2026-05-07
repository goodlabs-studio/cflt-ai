import type React from 'react';
import { useEffect, useMemo, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import type { ActivityEntry, IncidentMeta } from '@shared/types';
import { cn } from '@/lib/utils';

export function ActivityPage(): React.JSX.Element {
  const [entries, setEntries] = useState<ActivityEntry[]>([]);
  const [incidents, setIncidents] = useState<IncidentMeta[]>([]);
  const [skillFilter, setSkillFilter] = useState<string | null>(null);
  const [overlayFilter, setOverlayFilter] = useState<string | null>(null);
  const [activeIdx, setActiveIdx] = useState<number | null>(null);

  useEffect(() => {
    let mounted = true;
    Promise.all([
      window.cflt.fs.readActivity(),
      window.cflt.fs.listIncidents(),
    ])
      .then(([acts, incs]) => {
        if (!mounted) return;
        setEntries(acts);
        setIncidents(incs);
      })
      .catch(() => {
        /* gracefully render empty */
      });
    const dispose = window.cflt.fs.watch(
      ['wiki/activity/*.md', 'wiki/incidents/*.md'],
      () => {
        Promise.all([
          window.cflt.fs.readActivity(),
          window.cflt.fs.listIncidents(),
        ]).then(([acts, incs]) => {
          if (!mounted) return;
          setEntries(acts);
          setIncidents(incs);
        });
      },
    );
    return () => {
      mounted = false;
      dispose();
    };
  }, []);

  const skills = useMemo(() => {
    const set = new Set<string>();
    for (const e of entries) set.add(normalizeSkill(e.skill));
    return [...set].sort();
  }, [entries]);

  const overlays = useMemo(() => {
    const set = new Set<string>();
    for (const e of entries) {
      if (e.overlay) set.add(e.overlay);
    }
    return [...set].sort();
  }, [entries]);

  const filtered = useMemo(() => {
    return entries.filter((e) => {
      if (skillFilter && normalizeSkill(e.skill) !== skillFilter) return false;
      if (overlayFilter && e.overlay !== overlayFilter) return false;
      return true;
    });
  }, [entries, skillFilter, overlayFilter]);

  const activeEntry = activeIdx !== null ? filtered[activeIdx] ?? null : null;

  return (
    <div className="grid h-full grid-cols-[24rem_minmax(0,1fr)] overflow-hidden">
      <aside className="flex min-h-0 flex-col border-r border-border bg-muted/10">
        <FilterRow
          label="skill"
          options={skills}
          value={skillFilter}
          onChange={setSkillFilter}
        />
        <FilterRow
          label="overlay"
          options={overlays}
          value={overlayFilter}
          onChange={setOverlayFilter}
        />
        <ul className="flex-1 divide-y divide-border overflow-auto">
          {filtered.length === 0 && (
            <li className="p-4 text-xs text-muted-foreground/60">
              No activity matching the current filters.
            </li>
          )}
          {filtered.map((e, idx) => (
            <li key={`${e.timestamp}-${idx}`}>
              <button
                type="button"
                onClick={() => setActiveIdx(idx)}
                className={cn(
                  'flex w-full flex-col gap-1 px-3 py-2 text-left transition-colors',
                  activeIdx === idx ? 'bg-cflt-blue/10' : 'hover:bg-muted/40',
                )}
              >
                <div className="flex items-center justify-between gap-2">
                  <span className="font-mono text-[10px] text-muted-foreground">
                    {formatTimestamp(e.timestamp)}
                  </span>
                  <span className="rounded bg-muted px-1.5 py-0.5 font-mono text-[10px] text-muted-foreground">
                    {normalizeSkill(e.skill)}
                  </span>
                </div>
                {e.overlay && (
                  <div className="font-mono text-[10px] text-muted-foreground/70">
                    overlay: {e.overlay}
                  </div>
                )}
                {e.input && (
                  <div className="line-clamp-2 break-words text-[12px] text-foreground/80">
                    {stripPathPrefix(e.input)}
                  </div>
                )}
              </button>
            </li>
          ))}
        </ul>
        {incidents.length > 0 && (
          <footer className="border-t border-border bg-muted/20 px-3 py-2 text-[10px] uppercase tracking-wider text-warning">
            {incidents.length} incident{incidents.length === 1 ? '' : 's'} on file
          </footer>
        )}
      </aside>
      <div className="min-w-0 overflow-auto">
        {activeEntry ? (
          <EntryDetail entry={activeEntry} />
        ) : (
          <div className="flex h-full items-center justify-center text-sm text-muted-foreground">
            Select an entry to see provenance.
          </div>
        )}
      </div>
    </div>
  );
}

function FilterRow({
  label,
  options,
  value,
  onChange,
}: {
  label: string;
  options: string[];
  value: string | null;
  onChange: (v: string | null) => void;
}): React.JSX.Element {
  if (options.length === 0) return <div className="hidden" />;
  return (
    <div className="flex items-center gap-1.5 border-b border-border px-3 py-2 text-[10px]">
      <span className="uppercase tracking-wider text-muted-foreground/70">
        {label}
      </span>
      <button
        type="button"
        onClick={() => onChange(null)}
        className={cn(
          'rounded px-1.5 py-0.5',
          value === null
            ? 'bg-cflt-blue/15 text-foreground'
            : 'text-muted-foreground hover:bg-muted/60',
        )}
      >
        all
      </button>
      {options.map((o) => (
        <button
          key={o}
          type="button"
          onClick={() => onChange(o)}
          className={cn(
            'truncate rounded px-1.5 py-0.5 font-mono',
            value === o
              ? 'bg-cflt-blue/15 text-foreground'
              : 'text-muted-foreground hover:bg-muted/60',
          )}
          title={o}
        >
          {o}
        </button>
      ))}
    </div>
  );
}

function EntryDetail({ entry }: { entry: ActivityEntry }): React.JSX.Element {
  return (
    <div className="px-8 py-6">
      <header className="mb-4 border-b border-border pb-3">
        <div className="font-mono text-[11px] text-muted-foreground">
          {entry.timestamp}
        </div>
        <h1 className="text-xl font-semibold tracking-tight text-foreground">
          {normalizeSkill(entry.skill)}
        </h1>
      </header>
      <div className="wiki-prose">
        <ReactMarkdown remarkPlugins={[remarkGfm]}>{entry.raw}</ReactMarkdown>
      </div>
    </div>
  );
}

function normalizeSkill(s: string): string {
  // "/ask (--mode reconsolidate)" → "/ask"
  // "ad-hoc validation + authoring" → "ad-hoc"
  const trimmed = s.trim();
  if (trimmed.startsWith('/')) return trimmed.split(/\s/)[0];
  return trimmed.split(/\s+/)[0];
}

function stripPathPrefix(s: string): string {
  // De-noise long absolute paths in the rail preview
  return s.replace(/\/Users\/[^/]+\//g, '~/').replace(/\s+/g, ' ').trim();
}

function formatTimestamp(ts: string): string {
  // ISO "2026-04-30T12:00:00Z" → "04-30 12:00"
  const m = /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})/.exec(ts);
  return m ? `${m[2]}-${m[3]} ${m[4]}:${m[5]}` : ts;
}
