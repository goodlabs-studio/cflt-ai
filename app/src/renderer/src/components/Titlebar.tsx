import type React from 'react';
import { useEffect, useState } from 'react';
import { Settings, RefreshCw } from 'lucide-react';
import * as Tooltip from '@radix-ui/react-tooltip';
import { useMcp } from '@/store/mcp';
import {
  useConcurrency,
  initConcurrencySubscription,
} from '@/store/concurrency';

interface TitlebarProps {
  onOpenSettings?: () => void;
}

const EXPECTED_MCP_SERVERS = [
  'context7',
  'confluent-docs',
  'mcp-confluent',
  'terraform',
];

export function Titlebar({ onOpenSettings }: TitlebarProps = {}): React.JSX.Element {
  const [overlay, setOverlay] = useState<string>('base');
  const servers = useMcp((s) => s.servers);
  const lastUpdate = useMcp((s) => s.lastUpdate);
  const refreshing = useMcp((s) => s.refreshing);
  const refresh = useMcp((s) => s.refresh);
  const [profile] = useState<string>('read-only');
  const concurrency = useConcurrency();

  useEffect(() => {
    initConcurrencySubscription();
  }, []);

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
          FRANZ
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
          <Tooltip.Provider delayDuration={150}>
            <span className="no-drag flex items-center gap-1">
              {dots.map((d) => (
                <Tooltip.Root key={d.name}>
                  <Tooltip.Trigger asChild>
                    <span
                      className={
                        'no-drag block h-2 w-2 rounded-full ' +
                        (d.status === 'connected'
                          ? 'bg-success'
                          : d.status === 'failed'
                            ? 'bg-danger'
                            : d.status === 'needs-auth'
                              ? 'bg-warning'
                              : 'bg-muted-foreground/40')
                      }
                    />
                  </Tooltip.Trigger>
                  <Tooltip.Portal>
                    <Tooltip.Content
                      side="bottom"
                      sideOffset={6}
                      className="z-50 rounded border border-border bg-cflt-ink px-2 py-1 font-mono text-[11px] text-foreground shadow-md"
                    >
                      {d.name}: {d.status}
                      <Tooltip.Arrow className="fill-border" />
                    </Tooltip.Content>
                  </Tooltip.Portal>
                </Tooltip.Root>
              ))}
            </span>
          </Tooltip.Provider>
        </span>
        <Sep />
        <span>
          profile: <span className="text-foreground">{profile}</span>
        </span>
        {(concurrency.mutatingActive > 0 ||
          concurrency.nonMutatingActive > 0 ||
          concurrency.queueDepth > 0) && (
          <>
            <Sep />
            <span
              className="flex items-center gap-1"
              title={`mutating ${concurrency.mutatingActive}/1 · non-mutating ${concurrency.nonMutatingActive}/3 · queued ${concurrency.queueDepth}`}
            >
              <span className="text-muted-foreground">runs:</span>
              <span className="rounded bg-muted px-1.5 py-0.5 font-mono text-[10px] text-foreground">
                {concurrency.mutatingActive + concurrency.nonMutatingActive}
              </span>
              {concurrency.queueDepth > 0 && (
                <span className="rounded bg-warning/15 px-1.5 py-0.5 font-mono text-[10px] text-warning">
                  +{concurrency.queueDepth} queued
                </span>
              )}
            </span>
          </>
        )}
      </div>
      <div className="flex items-center gap-1">
        <button
          type="button"
          onClick={() => refresh()}
          disabled={refreshing}
          aria-label="Refresh MCP health"
          title="Refresh MCP health (⌘⇧R)"
          className="rounded p-1 text-muted-foreground hover:bg-muted hover:text-foreground disabled:opacity-40"
        >
          <RefreshCw className={refreshing ? 'h-3.5 w-3.5 animate-spin' : 'h-3.5 w-3.5'} />
        </button>
        <button
          type="button"
          onClick={onOpenSettings}
          aria-label="Settings"
          title="Settings (⌘,)"
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
