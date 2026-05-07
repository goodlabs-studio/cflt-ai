import type React from 'react';
import { useEffect, useState } from 'react';
import { Settings } from 'lucide-react';

interface McpDot {
  name: string;
  status: 'unknown' | 'ok' | 'fail';
}

const INITIAL_DOTS: McpDot[] = [
  { name: 'context7', status: 'unknown' },
  { name: 'confluent-docs', status: 'unknown' },
  { name: 'mcp-confluent', status: 'unknown' },
  { name: 'terraform', status: 'unknown' },
];

export function Titlebar(): React.JSX.Element {
  const [overlay, setOverlay] = useState<string>('base');
  const [dots] = useState<McpDot[]>(INITIAL_DOTS);
  const [profile] = useState<string>('read-only');

  useEffect(() => {
    let mounted = true;
    window.cflt.fs
      .activeLayers()
      .then((layers) => {
        if (mounted) setOverlay(layers.join(' + ') || 'base');
      })
      .catch(() => {
        /* ignore — Phase A stub returns ['base'] */
      });
    return () => {
      mounted = false;
    };
  }, []);

  return (
    <header className="titlebar-drag relative flex h-10 items-center justify-between border-b border-border bg-cflt-ink/60 px-4 text-xs">
      <div className="flex items-center gap-3 pl-16 text-muted-foreground">
        <span className="font-mono font-semibold tracking-tight text-foreground">
          cflt-ai
        </span>
        <Sep />
        <span>
          canon: <span className="text-foreground">{overlay}</span>
        </span>
        <Sep />
        <span className="flex items-center gap-1.5">
          MCP
          <span className="flex items-center gap-0.5">
            {dots.map((d) => (
              <span
                key={d.name}
                title={`${d.name}: ${d.status}`}
                className={
                  d.status === 'ok'
                    ? 'h-1.5 w-1.5 rounded-full bg-success'
                    : d.status === 'fail'
                      ? 'h-1.5 w-1.5 rounded-full bg-danger'
                      : 'h-1.5 w-1.5 rounded-full bg-muted-foreground/40'
                }
              />
            ))}
          </span>
        </span>
        <Sep />
        <span>
          profile: <span className="text-foreground">{profile}</span>
        </span>
      </div>
      <div className="flex items-center gap-2">
        <button
          type="button"
          aria-label="Settings"
          className="rounded p-1 text-muted-foreground hover:bg-muted hover:text-foreground"
        >
          <Settings className="h-3.5 w-3.5" />
        </button>
      </div>
    </header>
  );
}

function Sep(): React.JSX.Element {
  return <span className="text-border">·</span>;
}
