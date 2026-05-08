import type React from 'react';
import { useState } from 'react';
import { ChevronDown, ChevronRight, CheckCircle2, AlertTriangle, HelpCircle, Clock } from 'lucide-react';
import type { ParsedReview, ReviewClaim, ClaimVerdict } from '@shared/types';
import { cn } from '@/lib/utils';

interface Props {
  parsed: ParsedReview;
}

const CATEGORY_LABEL: Record<string, string> = {
  config_value: 'config',
  behavior_assertion: 'behavior',
  architecture_choice: 'arch',
  metric_sla: 'metric',
  comparison: 'compare',
};

export function ClaimTable({ parsed }: Props): React.JSX.Element {
  if (parsed.claims.length === 0) {
    return (
      <div className="rounded-md border border-dashed border-border p-6 text-center text-xs text-muted-foreground">
        Claim YAML block has not been emitted yet.
      </div>
    );
  }
  // Group claims by source file when multi-doc.
  const sources = [...new Set(parsed.claims.map((c) => c.sourceFile || '(unspecified)'))];
  const multi = sources.length > 1;

  return (
    <div className="space-y-4">
      <header className="flex items-center justify-between">
        <h3 className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground/70">
          Claims ({parsed.claims.length})
        </h3>
        <div className="flex items-center gap-2 text-[10px]">
          <Status
            label="YAML"
            ok={parsed.claimsComplete}
            okText="extracted"
            pendingText="streaming…"
          />
          <Status
            label="validation"
            ok={parsed.validationComplete}
            okText="merged"
            pendingText="awaiting…"
          />
        </div>
      </header>
      {multi ? (
        sources.map((src) => (
          <SourceGroup
            key={src}
            sourceLabel={src}
            claims={parsed.claims.filter((c) => (c.sourceFile || '(unspecified)') === src)}
          />
        ))
      ) : (
        <ClaimRows claims={parsed.claims} />
      )}
    </div>
  );
}

function SourceGroup({
  sourceLabel,
  claims,
}: {
  sourceLabel: string;
  claims: ReviewClaim[];
}): React.JSX.Element {
  return (
    <div>
      <div className="mb-1.5 font-mono text-[10px] uppercase tracking-wider text-muted-foreground/70">
        {sourceLabel}
      </div>
      <ClaimRows claims={claims} />
    </div>
  );
}

function ClaimRows({ claims }: { claims: ReviewClaim[] }): React.JSX.Element {
  return (
    <ul className="space-y-1.5">
      {claims.map((c) => (
        <ClaimRow key={c.id} claim={c} />
      ))}
    </ul>
  );
}

function ClaimRow({ claim }: { claim: ReviewClaim }): React.JSX.Element {
  const [open, setOpen] = useState(false);
  const hasEvidence =
    (claim.wikiSource && claim.wikiSource !== '—') ||
    (claim.mcpSource && claim.mcpSource !== '—');
  const verdict = claim.verdict ?? 'Pending';

  return (
    <li className="rounded border border-border bg-muted/20">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        disabled={!hasEvidence}
        className={cn(
          'flex w-full items-start gap-2.5 px-3 py-2 text-left text-[12px]',
          hasEvidence ? 'hover:bg-muted/40' : 'cursor-default',
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
        <div className="flex-1">
          <div className="flex flex-wrap items-center gap-1.5">
            <span className="rounded bg-muted px-1.5 py-0.5 font-mono text-[10px] text-muted-foreground">
              {claim.id}
            </span>
            <span className="rounded bg-cflt-blue/10 px-1.5 py-0.5 text-[10px] uppercase tracking-wider text-cflt-blue">
              {CATEGORY_LABEL[claim.category] ?? claim.category}
            </span>
            {claim.sourceSection && (
              <span className="text-[10px] text-muted-foreground/70">
                §{claim.sourceSection}
              </span>
            )}
          </div>
          <div className="mt-1 break-words text-foreground/90">{claim.text}</div>
        </div>
        <VerdictChip verdict={verdict} />
      </button>
      {open && hasEvidence && (
        <div className="border-t border-border bg-background/40 px-3 py-2 text-[11px]">
          <EvidenceRow label="Wiki" value={claim.wikiSource} />
          <EvidenceRow label="MCP" value={claim.mcpSource} />
        </div>
      )}
    </li>
  );
}

function EvidenceRow({
  label,
  value,
}: {
  label: string;
  value: string | undefined;
}): React.JSX.Element {
  return (
    <div className="flex gap-2 py-0.5">
      <span className="w-12 shrink-0 font-mono text-[10px] uppercase tracking-wider text-muted-foreground/70">
        {label}
      </span>
      <span className="break-words text-foreground/80">
        {value && value !== '—' ? value : <span className="text-muted-foreground/50">—</span>}
      </span>
    </div>
  );
}

const VERDICT_STYLE: Record<ClaimVerdict, { tone: string; icon: React.ComponentType<{ className?: string }>; }> = {
  Confirmed: { tone: 'bg-success/15 text-success', icon: CheckCircle2 },
  Corrected: { tone: 'bg-warning/15 text-warning', icon: AlertTriangle },
  Unverifiable: { tone: 'bg-danger/15 text-danger', icon: HelpCircle },
  Pending: { tone: 'bg-muted text-muted-foreground', icon: Clock },
};

function VerdictChip({ verdict }: { verdict: ClaimVerdict }): React.JSX.Element {
  const { tone, icon: Icon } = VERDICT_STYLE[verdict];
  return (
    <span
      className={cn(
        'inline-flex shrink-0 items-center gap-1 rounded px-1.5 py-0.5 text-[10px] uppercase tracking-wider',
        tone,
      )}
    >
      <Icon className="h-2.5 w-2.5" />
      {verdict}
    </span>
  );
}

function Status({
  label,
  ok,
  okText,
  pendingText,
}: {
  label: string;
  ok: boolean;
  okText: string;
  pendingText: string;
}): React.JSX.Element {
  return (
    <span
      className={cn(
        'rounded px-1.5 py-0.5 font-mono uppercase tracking-wider',
        ok ? 'bg-success/15 text-success' : 'bg-muted text-muted-foreground',
      )}
    >
      {label}: {ok ? okText : pendingText}
    </span>
  );
}
