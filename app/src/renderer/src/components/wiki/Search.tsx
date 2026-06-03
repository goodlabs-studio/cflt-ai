import type React from 'react';
import { useEffect, useRef, useState } from 'react';
import { Search as SearchIcon, X } from 'lucide-react';
import type { SearchHit } from '@shared/types';
import { cn } from '@/lib/utils';

/** Search box atop the Wiki sidebar. Empty value → parent shows the tree. */
export function WikiSearchInput({
  value,
  onChange,
}: {
  value: string;
  onChange: (v: string) => void;
}): React.JSX.Element {
  return (
    <div className="flex items-center gap-2 border-b border-border px-2.5 py-2">
      <SearchIcon className="h-3.5 w-3.5 shrink-0 text-muted-foreground" />
      <input
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder="Search the wiki…"
        className="w-full bg-transparent text-xs outline-none placeholder:text-muted-foreground/60"
      />
      {value && (
        <button
          type="button"
          onClick={() => onChange('')}
          className="shrink-0 text-muted-foreground hover:text-foreground"
          title="Clear search"
        >
          <X className="h-3.5 w-3.5" />
        </button>
      )}
    </div>
  );
}

/**
 * Ranked results from wiki-search.py (score order, as-is). Debounces the query
 * and guards against out-of-order responses; selecting a hit opens it in the
 * existing ArticleView via the shared onSelect handler.
 */
export function WikiSearchResults({
  query,
  activePath,
  onSelect,
}: {
  query: string;
  activePath: string | null;
  onSelect: (path: string) => void;
}): React.JSX.Element {
  const [hits, setHits] = useState<SearchHit[]>([]);
  const [loading, setLoading] = useState(false);
  const seq = useRef(0);

  useEffect(() => {
    const q = query.trim();
    if (!q) {
      setHits([]);
      return;
    }
    const mySeq = ++seq.current;
    setLoading(true);
    const timer = setTimeout(() => {
      window.cflt.tools
        .wikiSearch(q)
        .then((res) => {
          if (seq.current === mySeq) setHits(res);
        })
        .catch(() => {
          if (seq.current === mySeq) setHits([]);
        })
        .finally(() => {
          if (seq.current === mySeq) setLoading(false);
        });
    }, 150);
    return () => clearTimeout(timer);
  }, [query]);

  if (loading && hits.length === 0) {
    return <div className="px-3 py-4 text-xs text-muted-foreground/60">Searching…</div>;
  }
  if (hits.length === 0) {
    return (
      <div className="px-3 py-4 text-xs text-muted-foreground/60">
        No matches for “{query.trim()}”.
      </div>
    );
  }
  return (
    <ul className="space-y-0.5 p-2">
      {hits.map((h) => {
        const isActive = h.path === activePath;
        return (
          <li key={h.path}>
            <button
              type="button"
              onClick={() => onSelect(h.path)}
              className={cn(
                'flex w-full flex-col gap-0.5 rounded px-2 py-1.5 text-left transition-colors',
                isActive ? 'bg-cflt-blue/10' : 'hover:bg-muted/60',
              )}
            >
              <span className="truncate text-xs text-foreground">{label(h.path)}</span>
              {h.preview && (
                <span className="line-clamp-2 text-[10.5px] leading-snug text-muted-foreground/80">
                  {h.preview}
                </span>
              )}
            </button>
          </li>
        );
      })}
    </ul>
  );
}

/** wiki/concepts/sla-tiers.md → concepts/sla-tiers */
function label(path: string): string {
  return path.replace(/^wiki\//, '').replace(/\.md$/, '');
}
