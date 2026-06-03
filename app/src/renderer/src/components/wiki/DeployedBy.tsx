import type React from 'react';
import { Package, Play } from 'lucide-react';
import type { ManifestEntry } from '@shared/types';
import { cn } from '@/lib/utils';

const FSI_DSP_URI = /^fsi-dsp:\/\/(.+)$/;

/** Pull capability ids out of frontmatter `sources` (fsi-dsp://<id> URIs). */
export function assetIdsFromSources(sources: string[] | undefined): string[] {
  if (!sources) return [];
  return sources
    .map((s) => FSI_DSP_URI.exec(s.trim())?.[1])
    .filter((id): id is string => !!id);
}

/**
 * "Deployed by" panel: resolves the pattern's fsi-dsp:// source URIs against
 * MANIFEST.yaml and shows the implementing artifact(s). terraform-module
 * artifacts are executable today, so they get a "Plan this" deep-link; other
 * types are catalog-only until their executor lands (G.2).
 */
export function DeployedBy({
  sources,
  assets,
  onPlan,
}: {
  sources: string[] | undefined;
  assets: ManifestEntry[];
  onPlan?: (entry: ManifestEntry) => void;
}): React.JSX.Element | null {
  const ids = assetIdsFromSources(sources);
  // Only surface URIs that resolve to a real MANIFEST capability — fsi-dsp://
  // adr/* and doc refs are knowledge sources, not deployable assets.
  const entries = ids
    .map((id) => assets.find((a) => a.id === id))
    .filter((e): e is ManifestEntry => !!e);
  if (entries.length === 0) return null;

  return (
    <section className="rounded-md border border-border bg-muted/20 p-3 text-xs">
      <h3 className="mb-2 flex items-center gap-1.5 text-[10px] font-medium uppercase tracking-wider text-muted-foreground/70">
        <Package className="h-3 w-3" />
        Deployed by
      </h3>
      <ul className="space-y-2">
        {entries.map((e) => {
          const executable = e.type === 'terraform-module';
          return (
            <li
              key={e.id}
              className="rounded border border-border/60 bg-background/40 p-2"
            >
              <div className="flex items-center justify-between gap-2">
                <span className="font-mono text-[11px] text-foreground">{e.name}</span>
                <span
                  className={cn(
                    'shrink-0 rounded px-1 py-px font-mono text-[9px] uppercase tracking-wider',
                    executable
                      ? 'bg-cflt-blue/15 text-cflt-blue'
                      : 'bg-muted text-muted-foreground',
                  )}
                >
                  {e.type}
                </span>
              </div>
              {e.description && (
                <p className="mt-1 text-[10.5px] leading-snug text-muted-foreground/80">
                  {e.description}
                </p>
              )}
              {e.path && (
                <div
                  className="mt-1 truncate font-mono text-[10px] text-muted-foreground/60"
                  title={`raw/repos/fsi-dsp/${e.path}`}
                >
                  {e.path}
                </div>
              )}
              {executable ? (
                <button
                  type="button"
                  onClick={() => onPlan?.(e)}
                  className="mt-1.5 flex items-center gap-1 rounded bg-cflt-blue/15 px-1.5 py-0.5 text-[10px] uppercase tracking-wide text-cflt-blue hover:bg-cflt-blue/25"
                >
                  <Play className="h-2.5 w-2.5" />
                  Plan this
                </button>
              ) : (
                <div className="mt-1.5 text-[9.5px] italic text-muted-foreground/50">
                  catalog-only — executor lands G.2
                </div>
              )}
            </li>
          );
        })}
      </ul>
    </section>
  );
}
