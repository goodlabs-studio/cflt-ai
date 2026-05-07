import type React from 'react';
import { Loader2 } from 'lucide-react';
import type { ClaudeRoute } from '@shared/types';
import type { AskStatus } from '@/store/ask';
import { cn } from '@/lib/utils';

interface Props {
  status: AskStatus;
  route: ClaudeRoute | null;
}

const ROUTE_LABEL: Record<ClaudeRoute, string> = {
  wiki: 'wiki-only',
  mcp: 'wiki + MCP',
  deep: 'deep',
};

const ROUTE_TONE: Record<ClaudeRoute, string> = {
  wiki: 'bg-success/15 text-success',
  mcp: 'bg-cflt-blue/15 text-cflt-blue',
  deep: 'bg-warning/15 text-warning',
};

export function RouteBadge({ status, route }: Props): React.JSX.Element | null {
  if (status === 'idle') return null;
  if (status === 'classifying' || (route === null && status === 'streaming')) {
    return (
      <span className="inline-flex items-center gap-1.5 rounded bg-muted px-2 py-1 text-[11px] uppercase tracking-wider text-muted-foreground">
        <Loader2 className="h-3 w-3 animate-spin" />
        classifying…
      </span>
    );
  }
  if (route) {
    return (
      <span
        className={cn(
          'rounded px-2 py-1 text-[11px] uppercase tracking-wider',
          ROUTE_TONE[route],
        )}
      >
        route: {ROUTE_LABEL[route]}
      </span>
    );
  }
  return null;
}
