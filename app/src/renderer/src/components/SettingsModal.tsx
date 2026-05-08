import type React from 'react';
import { useEffect, useState } from 'react';
import * as Dialog from '@radix-ui/react-dialog';
import { Settings, X } from 'lucide-react';
import type { AskMode, ApplyProfile, UserConfig } from '@shared/types';
import { useUserConfig } from '@/store/config';
import { cn } from '@/lib/utils';

interface Props {
  open: boolean;
  onOpenChange: (v: boolean) => void;
}

const ASK_MODES: AskMode[] = ['ephemeral', 'report', 'reconsolidate'];
const PROFILES: ApplyProfile[] = ['read-only', 'engineer', 'break-glass'];

export function SettingsModal({ open, onOpenChange }: Props): React.JSX.Element {
  const config = useUserConfig((s) => s.config);
  const save = useUserConfig((s) => s.save);
  const load = useUserConfig((s) => s.load);
  const [draft, setDraft] = useState<UserConfig | null>(null);
  const [overlays, setOverlays] = useState<string[]>([]);

  useEffect(() => {
    if (open) {
      load();
      window.cflt.fs.listOverlays().then(setOverlays).catch(() => {});
    }
  }, [open, load]);

  useEffect(() => {
    if (config) setDraft(config);
  }, [config]);

  const onSave = async (): Promise<void> => {
    if (!draft) return;
    await save(draft);
    onOpenChange(false);
  };

  const set = <K extends keyof UserConfig>(key: K, value: UserConfig[K]): void => {
    setDraft((d) => (d ? { ...d, [key]: value } : d));
  };

  return (
    <Dialog.Root open={open} onOpenChange={onOpenChange}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-40 bg-black/50 backdrop-blur-sm" />
        <Dialog.Content className="fixed left-1/2 top-1/2 z-50 w-[32rem] -translate-x-1/2 -translate-y-1/2 rounded-lg border border-border bg-cflt-ink shadow-2xl">
          <Dialog.Title asChild>
            <header className="flex items-center gap-2 border-b border-border px-5 py-4">
              <Settings className="h-4 w-4 text-cflt-blue" />
              <span className="text-sm font-semibold text-foreground">Settings</span>
              <button
                type="button"
                onClick={() => onOpenChange(false)}
                className="ml-auto rounded p-1 text-muted-foreground hover:bg-muted hover:text-foreground"
                aria-label="Close"
              >
                <X className="h-3.5 w-3.5" />
              </button>
            </header>
          </Dialog.Title>

          {!draft ? (
            <div className="px-5 py-6 text-sm text-muted-foreground">
              Loading…
            </div>
          ) : (
            <div className="space-y-4 px-5 py-4 text-[12px]">
              <Field label="Max budget per skill invocation (USD)">
                <input
                  type="number"
                  min={0}
                  step={0.5}
                  value={draft.maxBudgetUsd}
                  onChange={(e) =>
                    set('maxBudgetUsd', Math.max(0, Number(e.target.value)))
                  }
                  className="w-32 rounded bg-muted px-2 py-1 text-foreground outline-none"
                />
                <Hint>
                  Passed as <span className="font-mono">--max-budget-usd</span> to
                  every <span className="font-mono">claude</span> subprocess.
                </Hint>
              </Field>

              <Field label="Default Ask mode">
                <Pills
                  options={ASK_MODES}
                  value={draft.defaultAskMode}
                  onChange={(v) => set('defaultAskMode', v)}
                />
              </Field>

              <Field label="Default Apply profile">
                <Pills
                  options={PROFILES}
                  value={draft.defaultApplyProfile}
                  onChange={(v) => set('defaultApplyProfile', v)}
                  tone={(p) =>
                    p === 'break-glass'
                      ? 'danger'
                      : p === 'engineer'
                        ? 'cflt-blue'
                        : 'muted'
                  }
                />
              </Field>

              <Field label="Default canon overlay">
                <select
                  value={draft.defaultOverlay}
                  onChange={(e) => set('defaultOverlay', e.target.value)}
                  className="rounded bg-muted px-2 py-1 text-foreground outline-none"
                >
                  <option value="">(base)</option>
                  {overlays.map((o) => (
                    <option key={o} value={o}>
                      {o}
                    </option>
                  ))}
                </select>
              </Field>
            </div>
          )}

          <footer className="flex items-center justify-end gap-2 border-t border-border px-5 py-3">
            <button
              type="button"
              onClick={() => onOpenChange(false)}
              className="rounded px-3 py-1.5 text-[12px] uppercase tracking-wide text-muted-foreground hover:bg-muted hover:text-foreground"
            >
              cancel
            </button>
            <button
              type="button"
              onClick={onSave}
              disabled={!draft}
              className="rounded bg-cflt-blue px-3 py-1.5 text-[12px] uppercase tracking-wide text-cflt-paper hover:opacity-90 disabled:opacity-40"
            >
              save
            </button>
          </footer>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}

function Field({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}): React.JSX.Element {
  return (
    <label className="block">
      <span className="mb-1 block text-[10px] font-semibold uppercase tracking-wider text-muted-foreground/70">
        {label}
      </span>
      {children}
    </label>
  );
}

function Hint({ children }: { children: React.ReactNode }): React.JSX.Element {
  return (
    <span className="ml-2 text-[11px] text-muted-foreground/70">{children}</span>
  );
}

function Pills<T extends string>({
  options,
  value,
  onChange,
  tone,
}: {
  options: readonly T[];
  value: T;
  onChange: (v: T) => void;
  tone?: (v: T) => 'danger' | 'cflt-blue' | 'muted';
}): React.JSX.Element {
  return (
    <div className="flex items-center gap-1 rounded bg-muted/60 p-0.5">
      {options.map((o) => {
        const active = o === value;
        const toneCls = tone?.(o);
        const activeTone =
          toneCls === 'danger'
            ? 'bg-danger/20 text-danger'
            : toneCls === 'cflt-blue'
              ? 'bg-cflt-blue/15 text-cflt-blue'
              : 'bg-background text-foreground';
        return (
          <button
            key={o}
            type="button"
            onClick={() => onChange(o)}
            className={cn(
              'rounded px-2 py-0.5 uppercase tracking-wide transition-colors',
              active
                ? activeTone
                : 'text-muted-foreground hover:text-foreground',
            )}
          >
            {o}
          </button>
        );
      })}
    </div>
  );
}
