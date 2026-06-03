import type React from 'react';
import { useEffect, useState } from 'react';
import mermaid from 'mermaid';

// Initialize once, themed to the FRANZ dark palette (cflt-ink / cflt-blue).
let initialized = false;
function initMermaid(): void {
  if (initialized) return;
  mermaid.initialize({
    startOnLoad: false,
    theme: 'dark',
    securityLevel: 'strict',
    fontFamily: 'ui-monospace, SFMono-Regular, monospace',
    themeVariables: {
      background: 'transparent',
      primaryColor: '#11212f',
      primaryBorderColor: '#2663eb',
      primaryTextColor: '#e5e9f0',
      lineColor: '#5b6b7d',
      secondaryColor: '#1a2430',
      tertiaryColor: '#0f1820',
    },
  });
  initialized = true;
}

// Unique, render-stable id per render() call — mermaid injects a temp DOM node
// keyed by this id, so collisions must be avoided.
let seq = 0;

/** Render a ```mermaid fenced block to themed SVG, client-side. */
export function Mermaid({ chart }: { chart: string }): React.JSX.Element {
  const [svg, setSvg] = useState('');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    initMermaid();
    mermaid
      .render(`mmd-${++seq}`, chart)
      .then((res) => {
        if (active) {
          setSvg(res.svg);
          setError(null);
        }
      })
      .catch((e: unknown) => {
        if (active) setError(e instanceof Error ? e.message : String(e));
      });
    return () => {
      active = false;
    };
  }, [chart]);

  if (error) {
    return (
      <div className="my-4 rounded border border-danger/40 bg-danger/10 p-3 text-xs text-danger">
        <div className="mb-1 font-medium">Mermaid render error</div>
        <pre className="whitespace-pre-wrap font-mono text-[11px]">{error}</pre>
      </div>
    );
  }

  return (
    <div
      className="my-4 flex justify-center overflow-x-auto rounded-md border border-border bg-cflt-ink/40 p-4 [&_svg]:h-auto [&_svg]:max-w-full"
      dangerouslySetInnerHTML={{ __html: svg }}
    />
  );
}
