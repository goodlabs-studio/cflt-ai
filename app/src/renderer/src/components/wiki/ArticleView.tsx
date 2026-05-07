import type React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeHighlight from 'rehype-highlight';
import type { WikiArticle, GraphEdge } from '@shared/types';
import { FrontmatterPanel } from './Frontmatter';
import { Backlinks } from './Backlinks';

interface Props {
  article: WikiArticle;
  edges: GraphEdge[];
  onNavigate?: (articleKey: string) => void;
}

export function ArticleView({
  article,
  edges,
  onNavigate,
}: Props): React.JSX.Element {
  const articleKey = article.path
    .replace(/^wiki\//, '')
    .replace(/\.md$/, '');
  const title =
    typeof article.frontmatter['title'] === 'string'
      ? (article.frontmatter['title'] as string)
      : articleKey;

  return (
    <div className="grid h-full grid-cols-[minmax(0,1fr)_18rem] gap-6 overflow-auto px-8 py-6">
      <article className="min-w-0">
        <header className="mb-6 border-b border-border pb-4">
          <div className="mb-1 font-mono text-[11px] text-muted-foreground">
            {article.path}
          </div>
          <h1 className="text-2xl font-semibold tracking-tight text-foreground">
            {title}
          </h1>
        </header>
        <div className="wiki-prose">
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            rehypePlugins={[rehypeHighlight]}
          >
            {article.body}
          </ReactMarkdown>
        </div>
      </article>
      <div className="space-y-5 pt-2">
        <FrontmatterPanel frontmatter={article.frontmatter} />
        <Backlinks
          edges={edges}
          articleKey={articleKey}
          onNavigate={onNavigate}
        />
      </div>
    </div>
  );
}
