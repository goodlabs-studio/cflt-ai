import type React from 'react';
import { useCallback, useEffect, useState } from 'react';
import type { GraphEdge, ManifestEntry, WikiArticle } from '@shared/types';
import { useNav } from '@/store/nav';
import { WikiTree } from '@/components/wiki/Tree';
import { WikiSearchInput, WikiSearchResults } from '@/components/wiki/Search';
import { ArticleView } from '@/components/wiki/ArticleView';

const DEFAULT_ARTICLE = 'wiki/concepts/sla-tiers.md';

export function WikiPage(): React.JSX.Element {
  const [activePath, setActivePath] = useState<string | null>(DEFAULT_ARTICLE);
  const [article, setArticle] = useState<WikiArticle | null>(null);
  const [edges, setEdges] = useState<GraphEdge[]>([]);
  const [assets, setAssets] = useState<ManifestEntry[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [query, setQuery] = useState('');
  const setPage = useNav((s) => s.setPage);
  const setPlanSeed = useNav((s) => s.setPlanSeed);

  // Load graph + fsi-dsp asset manifest once (both best-effort)
  useEffect(() => {
    let mounted = true;
    window.cflt.fs
      .readGraph()
      .then((g) => mounted && setEdges(g))
      .catch(() => {
        /* graph is best-effort */
      });
    window.cflt.fs
      .readManifest()
      .then((m) => mounted && setAssets(m))
      .catch(() => {
        /* manifest is best-effort (submodule may be absent) */
      });
    return () => {
      mounted = false;
    };
  }, []);

  // Deep-link an executable artifact into the Plan page, pre-seeded.
  const onPlanArtifact = useCallback(
    (entry: ManifestEntry) => {
      setPlanSeed(`Apply ${entry.name} (${entry.id}) — ${entry.description}`);
      setPage('plan');
    },
    [setPage, setPlanSeed],
  );

  // Load active article
  useEffect(() => {
    if (!activePath) return;
    let mounted = true;
    setArticle(null);
    setError(null);
    window.cflt.fs
      .readWiki(activePath)
      .then((a) => mounted && setArticle(a))
      .catch((e: Error) => mounted && setError(e.message));
    return () => {
      mounted = false;
    };
  }, [activePath]);

  // Backlinks navigation: edges use bare keys like "concepts/sla-tiers";
  // map back to "wiki/{key}.md" if the article exists.
  const onNavigate = useCallback((articleKey: string) => {
    setActivePath(`wiki/${articleKey}.md`);
  }, []);

  return (
    <div className="grid h-full grid-cols-[14rem_minmax(0,1fr)] overflow-hidden">
      <div className="flex min-h-0 flex-col border-r border-border bg-muted/10">
        <WikiSearchInput value={query} onChange={setQuery} />
        <div className="min-h-0 flex-1 overflow-auto">
          {query.trim() ? (
            <WikiSearchResults
              query={query}
              activePath={activePath}
              onSelect={setActivePath}
            />
          ) : (
            <WikiTree activePath={activePath} onSelect={setActivePath} />
          )}
        </div>
      </div>
      <div className="min-w-0 overflow-hidden">
        {error && (
          <div className="m-6 rounded border border-danger/40 bg-danger/10 p-4 text-sm text-danger">
            Failed to load article: {error}
          </div>
        )}
        {!error && article && (
          <ArticleView
            article={article}
            edges={edges}
            assets={assets}
            onNavigate={onNavigate}
            onPlanArtifact={onPlanArtifact}
          />
        )}
        {!error && !article && (
          <div className="flex h-full items-center justify-center text-sm text-muted-foreground">
            Loading…
          </div>
        )}
      </div>
    </div>
  );
}
