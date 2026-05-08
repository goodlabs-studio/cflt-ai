import type React from 'react';
import { useState } from 'react';
import * as Dialog from '@radix-ui/react-dialog';
import {
  AlertTriangle,
  ShieldAlert,
  ShieldCheck,
  Package,
  X,
  CheckCircle2,
  XCircle,
  CircleSlash,
  ChevronLeft,
} from 'lucide-react';
import type {
  ApplyConfirmation,
  ApplyProfile,
  GateInfo,
  PlanSummary,
  Profile,
} from '@shared/types';
import { cn } from '@/lib/utils';

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  plan: PlanSummary;
  profile: ApplyProfile;
  profileMeta?: Profile;
  onConfirm: (decision: ApplyConfirmation) => void;
}

const REASON_MIN = 20;

export function ConfirmationModal({
  open,
  onOpenChange,
  plan,
  profile,
  profileMeta,
  onConfirm,
}: Props): React.JSX.Element {
  // Two-step state for break-glass: 1=primary confirm + reason entry,
  //                                   2=final break-glass confirmation
  const [step, setStep] = useState<1 | 2>(1);
  const [reason, setReason] = useState('');

  const isBreakGlass = profile === 'break-glass';
  const allowed = profileMeta?.allowedOperations ?? [];
  const artifactId = plan.artifact?.id ?? '';
  const artifactPermitted =
    !artifactId ||
    profile === 'break-glass' ||
    allowed.includes(artifactId);
  const reasonValid = reason.trim().length >= REASON_MIN;

  const close = (): void => {
    onOpenChange(false);
    // Reset for next open
    setStep(1);
    setReason('');
  };

  const cancel = (): void => {
    onConfirm({ confirmed: false });
    close();
  };

  const proceedFromStep1 = (): void => {
    if (!artifactPermitted) return;
    if (isBreakGlass) {
      if (!reasonValid) return;
      setStep(2);
    } else {
      onConfirm({ confirmed: true });
      close();
    }
  };

  const finalBreakGlassConfirm = (): void => {
    onConfirm({ confirmed: true, reason: reason.trim() });
    close();
  };

  return (
    <Dialog.Root open={open} onOpenChange={(v) => (v ? onOpenChange(true) : cancel())}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm data-[state=open]:animate-in data-[state=closed]:animate-out" />
        <Dialog.Content
          onEscapeKeyDown={(e) => e.preventDefault()}
          onPointerDownOutside={(e) => e.preventDefault()}
          className="fixed left-1/2 top-1/2 z-50 flex max-h-[88vh] w-[42rem] -translate-x-1/2 -translate-y-1/2 flex-col rounded-lg border border-border bg-cflt-ink shadow-xl"
        >
          {step === 1 ? (
            <Step1Confirm
              plan={plan}
              profile={profile}
              profileMeta={profileMeta}
              isBreakGlass={isBreakGlass}
              artifactPermitted={artifactPermitted}
              reason={reason}
              setReason={setReason}
              reasonValid={reasonValid}
              onProceed={proceedFromStep1}
              onCancel={cancel}
            />
          ) : (
            <Step2BreakGlass
              plan={plan}
              reason={reason.trim()}
              onConfirm={finalBreakGlassConfirm}
              onBack={() => setStep(1)}
              onCancel={cancel}
            />
          )}
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}

// ─── Step 1: Standard confirmation ───────────────────────────────────────

function Step1Confirm({
  plan,
  profile,
  profileMeta,
  isBreakGlass,
  artifactPermitted,
  reason,
  setReason,
  reasonValid,
  onProceed,
  onCancel,
}: {
  plan: PlanSummary;
  profile: ApplyProfile;
  profileMeta?: Profile;
  isBreakGlass: boolean;
  artifactPermitted: boolean;
  reason: string;
  setReason: (s: string) => void;
  reasonValid: boolean;
  onProceed: () => void;
  onCancel: () => void;
}): React.JSX.Element {
  return (
    <>
      <Dialog.Title asChild>
        <header className="flex items-center gap-2 border-b border-border px-5 py-4">
          {isBreakGlass ? (
            <ShieldAlert className="h-5 w-5 text-danger" />
          ) : (
            <ShieldCheck className="h-5 w-5 text-cflt-blue" />
          )}
          <span className="text-base font-semibold tracking-tight text-foreground">
            {isBreakGlass ? 'Break-glass confirmation' : 'Apply confirmation'}
          </span>
          <ProfileBadge profile={profile} />
          <button
            type="button"
            onClick={onCancel}
            className="ml-auto rounded p-1 text-muted-foreground hover:bg-muted hover:text-foreground"
            aria-label="Cancel"
          >
            <X className="h-4 w-4" />
          </button>
        </header>
      </Dialog.Title>

      <div className="min-h-0 flex-1 space-y-4 overflow-auto px-5 py-4 text-[12px]">
        <ArtifactSection plan={plan} permitted={artifactPermitted} />
        <ArgumentsSection plan={plan} />
        <GatesSection gates={plan.gates ?? []} />
        <ProfileSection profile={profile} profileMeta={profileMeta} />
        {plan.provenance && (
          <div className="rounded border border-border bg-muted/15 p-2 font-mono text-[10px] text-muted-foreground">
            {plan.provenance}
          </div>
        )}

        {isBreakGlass && (
          <div className="rounded-md border border-danger/40 bg-danger/10 p-3">
            <div className="mb-1.5 flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-wider text-danger">
              <AlertTriangle className="h-3 w-3" />
              break-glass override reason
            </div>
            <textarea
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder={`Required. Min ${REASON_MIN} characters. Will be logged verbatim to wiki/activity/ and wiki/incidents/.`}
              className="min-h-[5rem] w-full resize-none rounded border border-border bg-background px-2 py-1.5 text-[12px] outline-none focus:border-danger"
            />
            <div className="mt-1 flex items-center justify-between text-[10px] text-muted-foreground">
              <span>{reason.trim().length} / {REASON_MIN} chars min</span>
              {reasonValid ? (
                <span className="text-success">ok</span>
              ) : (
                <span className="text-warning">need {REASON_MIN - reason.trim().length} more</span>
              )}
            </div>
          </div>
        )}

        {!artifactPermitted && (
          <div className="rounded-md border border-danger/40 bg-danger/10 p-3 text-[11px] text-danger">
            Profile <span className="font-mono">{profile}</span> does not permit{' '}
            <span className="font-mono">{plan.artifact?.id}</span>. Switch to a higher-tier profile or pick a different plan.
          </div>
        )}
      </div>

      <footer className="flex items-center justify-between border-t border-border px-5 py-3">
        <span className="text-[10px] text-muted-foreground">
          Press Esc to cancel. Click outside is disabled.
        </span>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={onCancel}
            className="rounded px-3 py-1.5 text-[12px] uppercase tracking-wide text-muted-foreground hover:bg-muted hover:text-foreground"
          >
            cancel
          </button>
          <button
            type="button"
            onClick={onProceed}
            disabled={
              !artifactPermitted || (isBreakGlass && !reasonValid)
            }
            className={cn(
              'rounded px-3 py-1.5 text-[12px] uppercase tracking-wide',
              isBreakGlass
                ? 'bg-danger text-cflt-paper hover:opacity-90 disabled:opacity-40'
                : 'bg-cflt-blue text-cflt-paper hover:opacity-90 disabled:opacity-40',
            )}
          >
            {isBreakGlass ? 'continue to break-glass' : 'CONFIRM APPLY'}
          </button>
        </div>
      </footer>
    </>
  );
}

// ─── Step 2: Final break-glass confirmation ─────────────────────────────

function Step2BreakGlass({
  plan,
  reason,
  onConfirm,
  onBack,
  onCancel,
}: {
  plan: PlanSummary;
  reason: string;
  onConfirm: () => void;
  onBack: () => void;
  onCancel: () => void;
}): React.JSX.Element {
  const artifactId = plan.artifact?.id ?? 'unknown';
  return (
    <>
      <Dialog.Title asChild>
        <header className="flex items-center gap-2 border-b border-danger/40 bg-danger/10 px-5 py-4">
          <ShieldAlert className="h-5 w-5 text-danger" />
          <span className="text-base font-semibold tracking-tight text-danger">
            CONFIRM BREAK-GLASS
          </span>
          <button
            type="button"
            onClick={onCancel}
            className="ml-auto rounded p-1 text-muted-foreground hover:bg-muted hover:text-foreground"
            aria-label="Cancel"
          >
            <X className="h-4 w-4" />
          </button>
        </header>
      </Dialog.Title>
      <div className="min-h-0 flex-1 space-y-3 overflow-auto px-5 py-4 text-[13px]">
        <p className="text-foreground">
          You are about to invoke{' '}
          <span className="font-mono text-danger">{artifactId}</span> under
          the <span className="font-mono text-danger">break-glass</span> profile.
        </p>
        <p className="text-muted-foreground">
          This bypasses the normal allowed-operations safety net. The
          override reason below is logged verbatim in both the activity log
          and the incident article and is reviewed in the post-incident audit.
        </p>
        <div className="rounded border border-danger/40 bg-danger/10 p-3">
          <div className="mb-1 text-[10px] font-semibold uppercase tracking-wider text-danger">
            override reason
          </div>
          <p className="whitespace-pre-wrap font-mono text-[12px] text-foreground">
            {reason}
          </p>
        </div>
      </div>
      <footer className="flex items-center justify-between border-t border-border px-5 py-3">
        <button
          type="button"
          onClick={onBack}
          className="flex items-center gap-1 rounded px-3 py-1.5 text-[12px] uppercase tracking-wide text-muted-foreground hover:bg-muted hover:text-foreground"
        >
          <ChevronLeft className="h-3 w-3" />
          back
        </button>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={onCancel}
            className="rounded px-3 py-1.5 text-[12px] uppercase tracking-wide text-muted-foreground hover:bg-muted hover:text-foreground"
          >
            cancel
          </button>
          <button
            type="button"
            onClick={onConfirm}
            className="rounded bg-danger px-3 py-1.5 text-[12px] uppercase tracking-wide text-cflt-paper hover:opacity-90"
          >
            CONFIRM BREAK-GLASS
          </button>
        </div>
      </footer>
    </>
  );
}

// ─── Sections inside step 1 ─────────────────────────────────────────────

function ArtifactSection({
  plan,
  permitted,
}: {
  plan: PlanSummary;
  permitted: boolean;
}): React.JSX.Element {
  return (
    <section>
      <SectionHeading icon={Package} label="Selected artifact" />
      {plan.artifact ? (
        <div className="space-y-0.5 rounded border border-border bg-muted/20 p-2">
          <Field
            label="id"
            value={plan.artifact.id}
            highlight={!permitted ? 'danger' : 'foreground'}
          />
          {plan.artifact.path && <Field label="path" value={plan.artifact.path} />}
          {plan.artifact.description && (
            <Field label="desc" value={plan.artifact.description} />
          )}
        </div>
      ) : (
        <div className="rounded border border-warning/40 bg-warning/10 p-2 text-[11px] text-warning">
          No artifact found in plan file. Apply will likely fail.
        </div>
      )}
    </section>
  );
}

function ArgumentsSection({ plan }: { plan: PlanSummary }): React.JSX.Element | null {
  if (!plan.arguments || plan.arguments.length === 0) return null;
  return (
    <section>
      <SectionHeading label="Arguments" />
      <div className="space-y-0.5 rounded border border-border bg-muted/20 p-2">
        {plan.arguments.map((a, i) => (
          <Field key={i} label={a.key} value={a.value} />
        ))}
      </div>
    </section>
  );
}

function GatesSection({ gates }: { gates: GateInfo[] }): React.JSX.Element | null {
  if (gates.length === 0) return null;
  return (
    <section>
      <SectionHeading label="Gate results (from plan)" />
      <ul className="space-y-1">
        {gates.map((g) => (
          <li
            key={g.name}
            className="flex items-center gap-2 rounded border border-border bg-muted/20 px-2 py-1.5 text-[11px]"
          >
            <GateStateIcon state={g.state} />
            <span className="font-mono text-muted-foreground">{g.name}</span>
            <span
              className={cn(
                'font-mono uppercase tracking-wider',
                g.state === 'pass'
                  ? 'text-success'
                  : g.state === 'fail'
                    ? 'text-danger'
                    : g.state === 'skipped'
                      ? 'text-warning'
                      : 'text-muted-foreground',
              )}
            >
              {g.state}
            </span>
            {g.detail && (
              <span className="ml-auto truncate text-muted-foreground/80">
                {g.detail}
              </span>
            )}
          </li>
        ))}
      </ul>
      <div className="mt-1 text-[10px] text-muted-foreground">
        These are gate states from the saved plan. Re-validation runs at apply time.
      </div>
    </section>
  );
}

function GateStateIcon({
  state,
}: {
  state: GateInfo['state'];
}): React.JSX.Element {
  if (state === 'pass') return <CheckCircle2 className="h-3 w-3 text-success" />;
  if (state === 'fail') return <XCircle className="h-3 w-3 text-danger" />;
  if (state === 'skipped') return <CircleSlash className="h-3 w-3 text-warning" />;
  return <CircleSlash className="h-3 w-3 text-muted-foreground/40" />;
}

function ProfileSection({
  profile,
  profileMeta,
}: {
  profile: ApplyProfile;
  profileMeta?: Profile;
}): React.JSX.Element {
  return (
    <section>
      <SectionHeading label="Profile" />
      <div className="rounded border border-border bg-muted/20 p-2">
        <div className="mb-1 flex items-center gap-2">
          <ProfileBadge profile={profile} />
          {profileMeta?.description && (
            <span className="text-[11px] text-muted-foreground">
              {profileMeta.description}
            </span>
          )}
        </div>
        <div className="text-[10px] uppercase tracking-wider text-muted-foreground/70">
          allowed operations ({profileMeta?.allowedOperations.length ?? 0})
        </div>
        <div className="mt-1 flex flex-wrap gap-1">
          {profileMeta?.allowedOperations.length === 0 && (
            <span className="text-[11px] italic text-muted-foreground/60">
              none — apply blocked
            </span>
          )}
          {profileMeta?.allowedOperations.map((op) => (
            <span
              key={op}
              className="rounded bg-muted px-1.5 py-0.5 font-mono text-[10px] text-muted-foreground"
            >
              {op}
            </span>
          ))}
        </div>
      </div>
    </section>
  );
}

function SectionHeading({
  label,
  icon: Icon,
}: {
  label: string;
  icon?: React.ComponentType<{ className?: string }>;
}): React.JSX.Element {
  return (
    <div className="mb-1.5 flex items-center gap-1 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground/70">
      {Icon && <Icon className="h-3 w-3" />}
      {label}
    </div>
  );
}

function Field({
  label,
  value,
  highlight = 'foreground',
}: {
  label: string;
  value: string;
  highlight?: 'foreground' | 'danger';
}): React.JSX.Element {
  return (
    <div className="flex gap-2 text-[11px]">
      <span className="w-14 shrink-0 font-mono uppercase tracking-wider text-muted-foreground/70">
        {label}
      </span>
      <span
        className={cn(
          'break-words font-mono',
          highlight === 'danger' ? 'text-danger' : 'text-foreground',
        )}
      >
        {value}
      </span>
    </div>
  );
}

function ProfileBadge({ profile }: { profile: ApplyProfile }): React.JSX.Element {
  const tone =
    profile === 'read-only'
      ? 'bg-muted text-muted-foreground'
      : profile === 'engineer'
        ? 'bg-cflt-blue/15 text-cflt-blue'
        : 'bg-danger/15 text-danger';
  return (
    <span
      className={cn(
        'rounded px-1.5 py-0.5 font-mono text-[10px] uppercase tracking-wider',
        tone,
      )}
    >
      {profile}
    </span>
  );
}
