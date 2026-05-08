import type React from 'react';
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import {
  PlayCircle,
  Square,
  ShieldAlert,
  ShieldCheck,
  AlertTriangle,
  ArrowRight,
} from 'lucide-react';
import type {
  ApplyProfile,
  PlanMeta,
  PlanSummary,
  Profile,
} from '@shared/types';
import { runSkill } from '@/lib/skill';
import { parsePlanFile } from '@/lib/apply-parse';
import { ConfirmationModal } from '@/components/apply/ConfirmationModal';
import { RunPanel, type RunPanelStatus } from '@/components/RunPanel';
import { cn } from '@/lib/utils';

const PROFILES: ApplyProfile[] = ['read-only', 'engineer', 'break-glass'];

interface RunState {
  status: RunPanelStatus;
  lines: string[];
  meta?: string;
  cancel?: () => void;
  activityRef?: string;
  incidentRef?: string;
}

const ACTIVITY_PATH_RE = /wiki\/activity\/\d{4}-\d{2}\.md/;
const INCIDENT_PATH_RE = /wiki\/incidents\/[A-Za-z0-9._-]+\.md/;

export function ApplyPage(): React.JSX.Element {
  const [plans, setPlans] = useState<PlanMeta[]>([]);
  const [activeSlug, setActiveSlug] = useState<string | null>(null);
  const [planSummary, setPlanSummary] = useState<PlanSummary | null>(null);
  const [profile, setProfile] = useState<ApplyProfile>('read-only');
  const [profileMetas, setProfileMetas] = useState<Record<string, Profile>>({});
  const [modalOpen, setModalOpen] = useState(false);
  const [run, setRun] = useState<RunState | null>(null);
  const cancelRef = useRef<(() => void) | null>(null);

  // Load plans + profile metadata on mount
  useEffect(() => {
    let mounted = true;
    const refresh = (): void => {
      window.cflt.fs.listPlans().then((p) => {
        if (!mounted) return;
        setPlans(p);
        if (!activeSlug && p.length > 0) setActiveSlug(p[0].slug);
      });
    };
    refresh();
    window.cflt.skill.listProfiles().then((profs) => {
      if (!mounted) return;
      const map: Record<string, Profile> = {};
      for (const p of profs) map[p.name] = p;
      setProfileMetas(map);
    });
    const dispose = window.cflt.fs.watch(['outputs/plans/*.md'], refresh);
    return () => {
      mounted = false;
      dispose();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Load active plan summary
  useEffect(() => {
    if (!activeSlug) {
      setPlanSummary(null);
      return;
    }
    const meta = plans.find((p) => p.slug === activeSlug);
    if (!meta) return;
    let mounted = true;
    window.cflt.fs.readPlan(meta.path).then((doc) => {
      if (!mounted) return;
      setPlanSummary(parsePlanFile(meta.slug, meta.path, doc.body));
    });
    return () => {
      mounted = false;
    };
  }, [activeSlug, plans]);

  const profileMeta = profileMetas[profile];

  const onApplyClick = useCallback(() => {
    if (!planSummary) return;
    if (profile === 'read-only') {
      setRun({
        status: 'error',
        lines: [
          `[blocked] profile=read-only does not permit any apply operations.`,
          `Switch to "engineer" or "break-glass" and re-run, or update tools/profiles/read-only.json.`,
        ],
        meta: 'blocked-by-profile',
      });
      return;
    }
    setModalOpen(true);
  }, [planSummary, profile]);

  const onConfirm = useCallback(
    async ({ confirmed, reason }: { confirmed: boolean; reason?: string }) => {
      if (!confirmed || !planSummary) return;
      const lines: string[] = [
        `▸ /dsp:apply --plan ${planSummary.path} --profile ${profile}${reason ? ` (break-glass)` : ''}`,
        ...(reason ? [`▸ override reason: ${reason}`] : []),
        `▸ activity log + incident article will record full provenance`,
      ];
      setRun({ status: 'running', lines });

      const handle = runSkill({
        kind: 'dsp:apply',
        planPath: planSummary.path,
        profile,
        ...(reason ? { operator: 'spicy-flute' } : {}),
      });
      cancelRef.current = handle.cancel;

      let activityRef: string | undefined;
      let incidentRef: string | undefined;

      try {
        for await (const ev of handle.events) {
          if (ev.type === 'assistant_text') {
            for (const piece of ev.text.split('\n')) {
              if (!piece) continue;
              lines.push(piece);
              if (!activityRef) {
                const m = ACTIVITY_PATH_RE.exec(piece);
                if (m) activityRef = m[0];
              }
              if (!incidentRef) {
                const m = INCIDENT_PATH_RE.exec(piece);
                if (m) incidentRef = m[0];
              }
            }
            setRun({ status: 'running', lines: [...lines], activityRef, incidentRef });
          } else if (ev.type === 'tool_use') {
            lines.push(`▸ tool_use ${ev.tool.name}`);
            setRun({ status: 'running', lines: [...lines], activityRef, incidentRef });
          } else if (ev.type === 'error') {
            lines.push(`[error] ${ev.message}`);
            setRun({ status: 'error', lines: [...lines], activityRef, incidentRef });
          } else if (ev.type === 'result') {
            cancelRef.current = null;
            const status: RunPanelStatus = ev.result.success ? 'success' : 'error';
            setRun({
              status,
              lines: [...lines],
              meta: `${ev.result.durationMs}ms · $${ev.result.costUsd.toFixed(4)}`,
              activityRef,
              incidentRef,
            });
            return;
          }
        }
      } catch (err) {
        const message = err instanceof Error ? err.message : String(err);
        lines.push(`[runtime] ${message}`);
        setRun({ status: 'error', lines: [...lines], activityRef, incidentRef });
      }
    },
    [planSummary, profile],
  );

  const isReadOnlyBlocked = profile === 'read-only';
  const isBreakGlass = profile === 'break-glass';
  const artifactPermitted =
    !planSummary?.artifact ||
    profile === 'break-glass' ||
    profileMeta?.allowedOperations.includes(planSummary.artifact.id);

  return (
    <div className="grid h-full grid-cols-[20rem_minmax(0,1fr)] gap-4 overflow-hidden p-4">
      <aside className="flex min-h-0 flex-col gap-3 overflow-auto">
        <PlanPicker
          plans={plans}
          activeSlug={activeSlug}
          onSelect={setActiveSlug}
        />
        <ProfileSelect
          profile={profile}
          onChange={setProfile}
          metas={profileMetas}
        />
        <ApplyControls
          canApply={!!planSummary && !isReadOnlyBlocked}
          isRunning={run?.status === 'running'}
          isBreakGlass={isBreakGlass}
          onApply={onApplyClick}
          onCancel={() => cancelRef.current?.()}
        />
        {planSummary && !artifactPermitted && profile !== 'read-only' && (
          <div className="flex items-start gap-2 rounded border border-warning/40 bg-warning/10 p-2 text-[11px] text-warning">
            <AlertTriangle className="mt-0.5 h-3 w-3 shrink-0" />
            <div>
              <span className="font-mono">{planSummary.artifact?.id}</span> is
              not in <span className="font-mono">{profile}</span>'s allowed
              operations. The apply will be blocked.
            </div>
          </div>
        )}
      </aside>

      <div className="flex min-h-0 flex-col gap-3 overflow-hidden">
        <PlanPreview plan={planSummary} />
        <div className="min-h-0 flex-1">
          {run ? (
            <RunPanel
              title={`/dsp:apply --profile ${profile}`}
              status={run.status}
              lines={run.lines}
              meta={run.meta}
              onCancel={
                run.status === 'running'
                  ? () => cancelRef.current?.()
                  : undefined
              }
              onClose={() => setRun(null)}
            />
          ) : (
            <div className="flex h-full items-center justify-center rounded-md border border-dashed border-border text-xs text-muted-foreground">
              Pick a plan and profile, then click Apply.
            </div>
          )}
          {run && (run.activityRef || run.incidentRef) && (
            <div className="mt-2 flex items-center gap-2 text-[11px]">
              {run.activityRef && (
                <RefChip label="activity" path={run.activityRef} />
              )}
              {run.incidentRef && (
                <RefChip label="incident" path={run.incidentRef} tone="danger" />
              )}
            </div>
          )}
        </div>
      </div>

      {planSummary && (
        <ConfirmationModal
          open={modalOpen}
          onOpenChange={setModalOpen}
          plan={planSummary}
          profile={profile}
          profileMeta={profileMeta}
          onConfirm={onConfirm}
        />
      )}
    </div>
  );
}

// ─── Sub-components ────────────────────────────────────────────────────

function PlanPicker({
  plans,
  activeSlug,
  onSelect,
}: {
  plans: PlanMeta[];
  activeSlug: string | null;
  onSelect: (slug: string) => void;
}): React.JSX.Element {
  return (
    <fieldset className="rounded-md border border-border bg-muted/20 p-3 text-[11px]">
      <legend className="px-1 text-[10px] uppercase tracking-wider text-muted-foreground/70">
        plan
      </legend>
      {plans.length === 0 ? (
        <div className="py-2 text-[11px] text-muted-foreground/60">
          No plans yet. Run /dsp:plan first.
        </div>
      ) : (
        <ul className="max-h-48 space-y-0.5 overflow-auto">
          {plans.map((p) => {
            const isActive = p.slug === activeSlug;
            return (
              <li key={p.slug}>
                <button
                  type="button"
                  onClick={() => onSelect(p.slug)}
                  className={cn(
                    'flex w-full items-center gap-1.5 rounded px-1.5 py-1 text-left transition-colors',
                    isActive
                      ? 'bg-cflt-blue/15 text-foreground'
                      : 'text-muted-foreground hover:bg-muted/40 hover:text-foreground',
                  )}
                >
                  <span className="font-mono text-[10px] text-muted-foreground/70">
                    {p.date ?? '—'}
                  </span>
                  <span className="truncate text-[11px]">{p.slug}</span>
                </button>
              </li>
            );
          })}
        </ul>
      )}
    </fieldset>
  );
}

function ProfileSelect({
  profile,
  onChange,
  metas,
}: {
  profile: ApplyProfile;
  onChange: (p: ApplyProfile) => void;
  metas: Record<string, Profile>;
}): React.JSX.Element {
  const meta = metas[profile];
  return (
    <fieldset className="space-y-2 rounded-md border border-border bg-muted/20 p-3 text-[11px]">
      <legend className="px-1 text-[10px] uppercase tracking-wider text-muted-foreground/70">
        profile
      </legend>
      <div className="flex items-center gap-1 rounded bg-muted/60 p-0.5">
        {PROFILES.map((p) => (
          <button
            key={p}
            type="button"
            onClick={() => onChange(p)}
            className={cn(
              'flex-1 rounded px-2 py-0.5 uppercase tracking-wide transition-colors',
              profile === p
                ? p === 'break-glass'
                  ? 'bg-danger/20 text-danger'
                  : p === 'engineer'
                    ? 'bg-cflt-blue/15 text-cflt-blue'
                    : 'bg-background text-foreground'
                : 'text-muted-foreground hover:text-foreground',
            )}
          >
            {p}
          </button>
        ))}
      </div>
      {meta && (
        <div className="space-y-1">
          {meta.description && (
            <p className="text-[11px] text-muted-foreground">
              {meta.description}
            </p>
          )}
          <div className="text-[10px] uppercase tracking-wider text-muted-foreground/70">
            allowed ({meta.allowedOperations.length})
          </div>
          {meta.allowedOperations.length === 0 ? (
            <div className="text-[11px] italic text-muted-foreground/60">
              none — apply blocked
            </div>
          ) : (
            <div className="flex flex-wrap gap-1">
              {meta.allowedOperations.map((op) => (
                <span
                  key={op}
                  className="rounded bg-muted px-1.5 py-0.5 font-mono text-[10px] text-muted-foreground"
                >
                  {op}
                </span>
              ))}
            </div>
          )}
        </div>
      )}
    </fieldset>
  );
}

function ApplyControls({
  canApply,
  isRunning,
  isBreakGlass,
  onApply,
  onCancel,
}: {
  canApply: boolean;
  isRunning: boolean;
  isBreakGlass: boolean;
  onApply: () => void;
  onCancel: () => void;
}): React.JSX.Element {
  if (isRunning) {
    return (
      <button
        type="button"
        onClick={onCancel}
        className="flex items-center justify-center gap-1 rounded bg-danger/15 px-2.5 py-2 text-[12px] uppercase tracking-wide text-danger hover:bg-danger/25"
      >
        <Square className="h-3 w-3" />
        cancel
      </button>
    );
  }
  return (
    <button
      type="button"
      onClick={onApply}
      disabled={!canApply}
      className={cn(
        'flex items-center justify-center gap-1.5 rounded px-2.5 py-2 text-[12px] uppercase tracking-wide text-cflt-paper hover:opacity-90 disabled:opacity-40',
        isBreakGlass ? 'bg-danger' : 'bg-cflt-blue',
      )}
    >
      {isBreakGlass ? (
        <ShieldAlert className="h-3.5 w-3.5" />
      ) : (
        <ShieldCheck className="h-3.5 w-3.5" />
      )}
      {isBreakGlass ? 'apply (break-glass)' : 'apply'}
      <ArrowRight className="h-3 w-3" />
    </button>
  );
}

function PlanPreview({
  plan,
}: {
  plan: PlanSummary | null;
}): React.JSX.Element {
  if (!plan) {
    return (
      <section className="rounded-md border border-dashed border-border p-3 text-center text-xs text-muted-foreground">
        Select a plan to preview.
      </section>
    );
  }
  return (
    <section className="rounded-md border border-border bg-muted/15 p-3">
      <div className="mb-1.5 flex items-center gap-2">
        <PlayCircle className="h-3.5 w-3.5 text-cflt-blue" />
        <h3 className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
          plan summary
        </h3>
        <span className="ml-auto font-mono text-[10px] text-muted-foreground">
          {plan.path}
        </span>
      </div>
      {plan.artifact && (
        <div className="mb-2 flex items-center gap-2 text-[12px]">
          <span className="font-mono text-foreground">{plan.artifact.id}</span>
          {plan.artifact.description && (
            <span className="text-muted-foreground">
              — {plan.artifact.description}
            </span>
          )}
        </div>
      )}
      {plan.gates && plan.gates.some((g) => g.state !== 'pending') && (
        <div className="flex flex-wrap items-center gap-1">
          {plan.gates.map((g) => (
            <span
              key={g.name}
              className={cn(
                'rounded px-1.5 py-0.5 font-mono text-[10px]',
                g.state === 'pass'
                  ? 'bg-success/15 text-success'
                  : g.state === 'fail'
                    ? 'bg-danger/15 text-danger'
                    : g.state === 'skipped'
                      ? 'bg-warning/15 text-warning'
                      : 'bg-muted text-muted-foreground',
              )}
            >
              {g.name}: {g.state}
            </span>
          ))}
        </div>
      )}
    </section>
  );
}

function RefChip({
  label,
  path,
  tone,
}: {
  label: string;
  path: string;
  tone?: 'danger';
}): React.JSX.Element {
  return (
    <span
      className={cn(
        'flex items-center gap-1 rounded px-2 py-0.5 font-mono text-[10px]',
        tone === 'danger'
          ? 'bg-danger/15 text-danger'
          : 'bg-muted text-muted-foreground',
      )}
      title={path}
    >
      {label}: {path.split('/').slice(-1)[0]}
    </span>
  );
}
