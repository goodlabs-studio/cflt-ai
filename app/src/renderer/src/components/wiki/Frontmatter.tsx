import type React from 'react';
import type { WikiArticleFrontmatter } from '@shared/types';
import { cn } from '@/lib/utils';

interface Props {
  frontmatter: WikiArticleFrontmatter;
}

const CONFIDENCE_STYLE: Record<string, string> = {
  high: 'bg-success/15 text-success',
  medium: 'bg-warning/15 text-warning',
  low: 'bg-danger/15 text-danger',
};

export function FrontmatterPanel({ frontmatter: f }: Props): React.JSX.Element {
  const tags = (f.tags ?? []) as string[];
  const sources = (f.sources ?? []) as string[];
  const related = (f.related ?? []) as string[];
  const decay = computeDecay(f.last_validated, f.confidence);

  return (
    <aside className="space-y-5 text-xs">
      {f.confidence && (
        <Field label="Confidence">
          <span
            className={cn(
              'inline-block rounded px-1.5 py-0.5 text-[10px] uppercase tracking-wide',
              CONFIDENCE_STYLE[f.confidence] ?? 'bg-muted text-muted-foreground',
            )}
          >
            {f.confidence}
          </span>
        </Field>
      )}

      {f.last_updated && (
        <Field label="Updated">
          <span className="font-mono">{f.last_updated}</span>
        </Field>
      )}

      {f.last_validated && (
        <Field label="Validated">
          <div className="flex items-center gap-2">
            <span className="font-mono">{f.last_validated}</span>
            {decay && (
              <span className="rounded bg-warning/15 px-1.5 py-0.5 text-[10px] text-warning">
                {decay}
              </span>
            )}
          </div>
        </Field>
      )}

      {tags.length > 0 && (
        <Field label="Tags">
          <div className="flex flex-wrap gap-1">
            {tags.map((t) => (
              <span
                key={t}
                className="rounded bg-muted px-1.5 py-0.5 font-mono text-[10px] text-muted-foreground"
              >
                #{t}
              </span>
            ))}
          </div>
        </Field>
      )}

      {sources.length > 0 && (
        <Field label="Sources">
          <ul className="space-y-1">
            {sources.map((s, i) => (
              <li key={i} className="break-all text-muted-foreground">
                {s}
              </li>
            ))}
          </ul>
        </Field>
      )}

      {related.length > 0 && (
        <Field label="Related">
          <ul className="space-y-1">
            {related.map((r) => (
              <li key={r} className="font-mono text-muted-foreground">
                {r}
              </li>
            ))}
          </ul>
        </Field>
      )}
    </aside>
  );
}

function Field({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}): React.JSX.Element {
  return (
    <div>
      <div className="mb-1.5 text-[10px] font-medium uppercase tracking-wider text-muted-foreground/70">
        {label}
      </div>
      <div>{children}</div>
    </div>
  );
}

/**
 * Wiki canon: high-confidence articles past 90 days without revalidation
 * carry a "decay" warning. Returns a short label or null.
 */
function computeDecay(
  lastValidated: string | undefined,
  confidence: string | undefined,
): string | null {
  if (!lastValidated || confidence !== 'high') return null;
  const validated = Date.parse(lastValidated);
  if (Number.isNaN(validated)) return null;
  const days = Math.floor((Date.now() - validated) / 86_400_000);
  if (days > 90) return `${days}d stale`;
  return null;
}
