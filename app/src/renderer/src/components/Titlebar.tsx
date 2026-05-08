import type React from 'react';
import { useEffect, useState } from 'react';
import { Settings } from 'lucide-react';
import { useMcp } from '@/store/mcp';

const EXPECTED_MCP_SERVERS = [
  'context7',
  'confluent-docs',
  'mcp-confluent',
  'terraform',
];

export function Titlebar(): React.JSX.Element {
  const [overlay, setOverlay] = useState<string>('base');
  const servers = useMcp((s) => s.servers);
  const lastUpdate = useMcp((s) => s.lastUpdate);
  const [profile] = useState<string>('read-only');

  // Render dots in expected order; merge in any extra servers we see.
  const seen = new Set(servers.map((s) => s.name));
  const dots = [
    ...EXPECTED_MCP_SERVERS.map((name) => {
      const match = servers.find((s) => s.name === name);
      return {
        name,
        status: match?.status ?? 'unknown',
      };
    }),
    ...servers.filter((s) => !EXPECTED_MCP_SERVERS.includes(s.name) && seen.has(s.name)),
  ];

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
        <span
          className="flex items-center gap-1.5"
          title={
            lastUpdate
              ? `Last MCP probe: ${new Date(lastUpdate).toLocaleTimeString()}`
              : 'MCP health populates after first skill run'
          }
        >
          MCP
          <span className="flex items-center gap-0.5">
            {dots.map((d) => (
              <span
                key={d.name}
                title={`${d.name}: ${d.status}`}
                className={
                  d.status === 'connected'
                    ? 'h-1.5 w-1.5 rounded-full bg-success'
                    : d.status === 'failed'
                      ? 'h-1.5 w-1.5 rounded-full bg-danger'
                      : d.status === 'needs-auth'
                        ? 'h-1.5 w-1.5 rounded-full bg-warning'
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
