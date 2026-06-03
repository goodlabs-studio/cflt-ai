import type React from 'react';
import ReactMarkdown, { type Components } from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeHighlight from 'rehype-highlight';
import type { WikiArticle, GraphEdge, ManifestEntry } from '@shared/types';
import { FrontmatterPanel } from './Frontmatter';
import { Backlinks } from './Backlinks';
import { DeployedBy } from './DeployedBy';
import { Mermaid } from './Mermaid';

/** Flatten React children (incl. rehype-highlight spans) back to source text. */
function nodeText(node: React.ReactNode): string {
  if (node == null || typeof node === 'boolean') return '';
  if (typeof node === 'string' || typeof node === 'number') return String(node);
  if (Array.isArray(node)) return node.map(nodeText).join('');
  if (typeof node === 'object' && 'props' in node) {
    return nodeText((node as { props?: { children?: React.ReactNode } }).props?.children);
  }
  return '';
}

// Intercept ```mermaid fences and render them as diagrams; everything else
// keeps the default code/pre rendering (with highlight classes intact).
const markdownComponents: Components = {
  code(props) {
    const { className, children } = props;
    if (/\blanguage-mermaid\b/.test(className ?? '')) {
      return <Mermaid chart={nodeText(children).replace(/\n+$/, '')} />;
    }
    return <code className={className}>{children}</code>;
  },
  pre(props) {
    const { children, node } = props as {
      children?: React.ReactNode;
      node?: { children?: Array<{ properties?: { className?: unknown } }> };
    };
    const cls = node?.children?.[0]?.properties?.className;
    // Mermaid renders its own framed block — drop the <pre> card wrapper.
    if (Array.isArray(cls) && cls.includes('language-mermaid')) {
      return <>{children}</>;
    }
    return <pre>{children}</pre>;
  },
};

interface Props {
  article: WikiArticle;
  edges: GraphEdge[];
  assets: ManifestEntry[];
  onNavigate?: (articleKey: string) => void;
  onPlanArtifact?: (entry: ManifestEntry) => void;
}

export function ArticleView({
  article,
  edges,
  assets,
  onNavigate,
  onPlanArtifact,
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
            rehypePlugins={[[rehypeHighlight, { ignoreMissing: true }]]}
            components={markdownComponents}
          >
            {article.body}
          </ReactMarkdown>
        </div>
      </article>
      <div className="space-y-5 pt-2">
        <FrontmatterPanel frontmatter={article.frontmatter} />
        <DeployedBy
          sources={article.frontmatter.sources}
          assets={assets}
          onPlan={onPlanArtifact}
        />
        <Backlinks
          edges={edges}
          articleKey={articleKey}
          onNavigate={onNavigate}
        />
      </div>
    </div>
  );
}
