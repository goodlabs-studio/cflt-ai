import type React from 'react';
import { useCallback, useEffect, useState } from 'react';
import type { GraphEdge, WikiArticle } from '@shared/types';
import { WikiTree } from '@/components/wiki/Tree';
import { ArticleView } from '@/components/wiki/ArticleView';

const DEFAULT_ARTICLE = 'wiki/concepts/sla-tiers.md';

export function WikiPage(): React.JSX.Element {
  const [activePath, setActivePath] = useState<string | null>(DEFAULT_ARTICLE);
  const [article, setArticle] = useState<WikiArticle | null>(null);
  const [edges, setEdges] = useState<GraphEdge[]>([]);
  const [error, setError] = useState<string | null>(null);

  // Load graph once
  useEffect(() => {
    let mounted = true;
    window.cflt.fs
      .readGraph()
      .then((g) => mounted && setEdges(g))
      .catch(() => {
        /* graph is best-effort */
      });
    return () => {
      mounted = false;
    };
  }, []);

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
      <div className="overflow-auto border-r border-border bg-muted/10">
        <WikiTree activePath={activePath} onSelect={setActivePath} />
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
            onNavigate={onNavigate}
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
