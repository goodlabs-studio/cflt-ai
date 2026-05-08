import type React from 'react';
import { useState } from 'react';
import {
  CheckCircle2,
  XCircle,
  Loader2,
  CircleSlash,
  Circle,
  ChevronRight,
  ChevronDown,
} from 'lucide-react';
import type { GateInfo, GateState } from '@shared/types';
import { cn } from '@/lib/utils';

interface Props {
  gates: GateInfo[];
}

const GATE_LABEL: Record<string, string> = {
  canon_compliance: 'Canon',
  fsi_dsp_coverage: 'fsi-dsp',
  confluent_docs_schema: 'Schema',
  mcp_confluent_state: 'Cluster',
};

const STATE_STYLE: Record<
  GateState,
  { tone: string; icon: React.ComponentType<{ className?: string }> }
> = {
  pending: { tone: 'border-border bg-muted/40 text-muted-foreground/60', icon: Circle },
  running: { tone: 'border-cflt-blue/60 bg-cflt-blue/15 text-cflt-blue', icon: Loader2 },
  pass: { tone: 'border-success/40 bg-success/10 text-success', icon: CheckCircle2 },
  fail: { tone: 'border-danger/40 bg-danger/10 text-danger', icon: XCircle },
  skipped: { tone: 'border-warning/40 bg-warning/10 text-warning', icon: CircleSlash },
};

export function GateChain({ gates }: Props): React.JSX.Element {
  return (
    <div className="space-y-2">
      <div className="flex items-stretch gap-1">
        {gates.map((g, i) => (
          <div key={g.name} className="flex flex-1 items-stretch gap-1">
            <GateChip gate={g} />
            {i < gates.length - 1 && (
              <ChevronRight className="h-3 w-3 self-center text-muted-foreground/40" />
            )}
          </div>
        ))}
      </div>
      <div className="space-y-1">
        {gates
          .filter((g) => g.state !== 'pending')
          .map((g) => (
            <GateRow key={g.name} gate={g} />
          ))}
      </div>
    </div>
  );
}

function GateChip({ gate }: { gate: GateInfo }): React.JSX.Element {
  const { tone, icon: Icon } = STATE_STYLE[gate.state];
  const animate = gate.state === 'running';
  return (
    <div
      className={cn(
        'flex flex-1 flex-col items-center gap-1 rounded-md border px-2 py-2 transition-colors',
        tone,
      )}
      title={`${gate.name}: ${gate.state}${gate.detail ? ` — ${gate.detail}` : ''}`}
    >
      <Icon className={cn('h-4 w-4', animate && 'animate-spin')} />
      <div className="font-mono text-[10px] uppercase tracking-wider">
        {GATE_LABEL[gate.name] ?? gate.name}
      </div>
      <div className="font-mono text-[10px] uppercase tracking-wider opacity-75">
        {gate.state}
      </div>
    </div>
  );
}

function GateRow({ gate }: { gate: GateInfo }): React.JSX.Element {
  const [open, setOpen] = useState(false);
  const hasEvidence = gate.evidence && gate.evidence.length > 0;
  const { tone, icon: Icon } = STATE_STYLE[gate.state];

  return (
    <div className="rounded border border-border bg-muted/15">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        disabled={!hasEvidence}
        className={cn(
          'flex w-full items-start gap-2 px-3 py-2 text-left text-[12px]',
          hasEvidence ? 'hover:bg-muted/30' : 'cursor-default',
        )}
      >
        <div className="mt-0.5">
          {hasEvidence ? (
            open ? (
              <ChevronDown className="h-3 w-3 text-muted-foreground" />
            ) : (
              <ChevronRight className="h-3 w-3 text-muted-foreground" />
            )
          ) : (
            <ChevronRight className="h-3 w-3 text-muted-foreground/30" />
          )}
        </div>
        <span
          className={cn(
            'inline-flex shrink-0 items-center gap-1 rounded px-1.5 py-0.5 text-[10px] uppercase tracking-wider',
            tone,
          )}
        >
          <Icon className="h-2.5 w-2.5" />
          {gate.state}
        </span>
        <span className="font-mono text-[11px] text-muted-foreground">
          {gate.name}
        </span>
        <span className="flex-1 text-foreground/80">{gate.detail ?? ''}</span>
      </button>
      {open && hasEvidence && (
        <div className="border-t border-border bg-background/40 px-3 py-2 text-[11px] font-mono text-muted-foreground">
          <ul className="space-y-0.5">
            {gate.evidence!.map((e, i) => (
              <li key={i} className="break-words">
                · {e}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
