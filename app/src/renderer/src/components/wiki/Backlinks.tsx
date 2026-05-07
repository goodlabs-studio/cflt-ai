import type React from 'react';
import { ArrowRight } from 'lucide-react';
import type { GraphEdge } from '@shared/types';

interface Props {
  edges: GraphEdge[];
  /** Article path stripped of "wiki/" prefix and ".md" suffix. */
  articleKey: string;
  onNavigate?: (articleKey: string) => void;
}

export function Backlinks({
  edges,
  articleKey,
  onNavigate,
}: Props): React.JSX.Element | null {
  const out = edges.filter((e) => e.source === articleKey);
  const inbound = edges.filter((e) => e.target === articleKey);
  if (out.length === 0 && inbound.length === 0) return null;

  return (
    <section className="rounded-md border border-border bg-muted/20 p-3 text-xs">
      <h3 className="mb-2 text-[10px] font-medium uppercase tracking-wider text-muted-foreground/70">
        Backlinks
      </h3>
      {out.length > 0 && (
        <Group label="Outgoing" edges={out} side="target" onNavigate={onNavigate} />
      )}
      {inbound.length > 0 && (
        <Group
          label="Incoming"
          edges={inbound}
          side="source"
          onNavigate={onNavigate}
        />
      )}
    </section>
  );
}

function Group({
  label,
  edges,
  side,
  onNavigate,
}: {
  label: string;
  edges: GraphEdge[];
  side: 'source' | 'target';
  onNavigate?: (k: string) => void;
}): React.JSX.Element {
  return (
    <div className="mb-2 last:mb-0">
      <div className="mb-1 text-[10px] uppercase tracking-wider text-muted-foreground/60">
        {label}
      </div>
      <ul className="space-y-1.5">
        {edges.map((e, i) => {
          const k = e[side];
          return (
            <li key={i} className="flex items-start gap-1.5">
              <ArrowRight className="mt-0.5 h-3 w-3 shrink-0 text-cflt-blue/70" />
              <button
                type="button"
                onClick={() => onNavigate?.(k)}
                className="flex-1 text-left text-muted-foreground hover:text-foreground"
              >
                <div className="font-mono text-[11px] text-foreground">{k}</div>
                <div className="text-[11px] leading-snug">{e.relationship}</div>
              </button>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
