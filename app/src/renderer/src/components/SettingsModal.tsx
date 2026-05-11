import type React from 'react';
import { useEffect, useMemo, useState } from 'react';
import * as Dialog from '@radix-ui/react-dialog';
import { Settings, X, Plus, Trash2 } from 'lucide-react';
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
        <Dialog.Content className="fixed left-1/2 top-1/2 z-50 flex max-h-[85vh] w-[36rem] max-w-[calc(100vw-2rem)] -translate-x-1/2 -translate-y-1/2 flex-col rounded-lg border border-border bg-cflt-ink shadow-2xl">
          <Dialog.Title asChild>
            <header className="flex shrink-0 items-center gap-2 border-b border-border px-5 py-4">
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
            <div className="flex-1 space-y-4 overflow-y-auto px-5 py-4 text-[12px]">
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

              <div className="border-t border-border pt-3">
                <EnvVarsEditor
                  vars={draft.mcpEnvVars ?? {}}
                  onChange={(vars) => set('mcpEnvVars', vars)}
                />
              </div>
            </div>
          )}

          <footer className="flex shrink-0 items-center justify-end gap-2 border-t border-border px-5 py-3">
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

// Named fields for the env vars mcp-confluent actually consumes (per
// @confluentinc/mcp-confluent 1.2.x README). Grouped by what each set
// enables — fill any one group and the corresponding feature lights up.
const FIELD_GROUPS: ReadonlyArray<{
  title: string;
  hint: string;
  fields: ReadonlyArray<{
    key: string;
    label: string;
    secret?: boolean;
    placeholder?: string;
  }>;
}> = [
  {
    title: 'Confluent Cloud (control plane)',
    hint: 'Manages topics, clusters, schemas via the Cloud REST API. This is the minimum for mcp-confluent to flip green.',
    fields: [
      { key: 'CONFLUENT_CLOUD_API_KEY', label: 'Cloud API key' },
      { key: 'CONFLUENT_CLOUD_API_SECRET', label: 'Cloud API secret', secret: true },
      {
        key: 'CONFLUENT_CLOUD_REST_ENDPOINT',
        label: 'Cloud REST endpoint',
        placeholder: 'https://api.confluent.cloud',
      },
    ],
  },
  {
    title: 'Kafka cluster (data plane)',
    hint: 'Required only for produce/consume operations on a specific cluster.',
    fields: [
      {
        key: 'BOOTSTRAP_SERVERS',
        label: 'Bootstrap servers',
        placeholder: 'pkc-xxxxx.region.provider.confluent.cloud:9092',
      },
      { key: 'KAFKA_API_KEY', label: 'Kafka API key' },
      { key: 'KAFKA_API_SECRET', label: 'Kafka API secret', secret: true },
      { key: 'KAFKA_CLUSTER_ID', label: 'Cluster ID', placeholder: 'lkc-xxxxx' },
    ],
  },
  {
    title: 'Schema Registry',
    hint: 'Required for schema lookups and Avro/Protobuf metadata.',
    fields: [
      {
        key: 'SCHEMA_REGISTRY_ENDPOINT',
        label: 'Endpoint',
        placeholder: 'https://psrc-xxxxx.region.provider.confluent.cloud',
      },
      { key: 'SCHEMA_REGISTRY_API_KEY', label: 'API key' },
      { key: 'SCHEMA_REGISTRY_API_SECRET', label: 'API secret', secret: true },
    ],
  },
  {
    title: 'Flink (Confluent Cloud)',
    hint: 'Required only for Flink SQL skill flows.',
    fields: [
      { key: 'FLINK_API_KEY', label: 'Flink API key' },
      { key: 'FLINK_API_SECRET', label: 'Flink API secret', secret: true },
      {
        key: 'FLINK_REST_ENDPOINT',
        label: 'Flink REST endpoint',
        placeholder: 'https://flink.region.provider.confluent.cloud',
      },
      { key: 'FLINK_COMPUTE_POOL_ID', label: 'Compute pool ID', placeholder: 'lfcp-xxxxx' },
      { key: 'FLINK_ENV_ID', label: 'Environment ID', placeholder: 'env-xxxxx' },
    ],
  },
];

const KNOWN_KEYS = new Set(
  FIELD_GROUPS.flatMap((g) => g.fields.map((f) => f.key)),
);

interface Row {
  id: number;
  key: string;
  value: string;
}

let rowSeq = 0;

function EnvVarsEditor({
  vars,
  onChange,
}: {
  vars: Record<string, string>;
  onChange: (v: Record<string, string>) => void;
}): React.JSX.Element {
  // Saved vars are split into two surfaces by name: known keys feed the
  // named fields, unknown keys feed the "Other" rows. Each surface owns
  // its key exclusively — overlap would let a delete on one surface
  // silently keep the value alive on the other.
  const [values, setValues] = useState<Record<string, string>>(() =>
    Object.fromEntries(
      Object.entries(vars).filter(([k]) => KNOWN_KEYS.has(k)),
    ),
  );
  const [otherRows, setOtherRows] = useState<Row[]>(() =>
    Object.entries(vars)
      .filter(([k]) => !KNOWN_KEYS.has(k))
      .map(([k, v]) => ({ id: ++rowSeq, key: k, value: v })),
  );

  const flush = (
    nextValues: Record<string, string>,
    nextOther: Row[],
  ): void => {
    setValues(nextValues);
    setOtherRows(nextOther);
    const out: Record<string, string> = {};
    for (const [k, v] of Object.entries(nextValues)) {
      if (k.trim() && v.trim()) out[k.trim()] = v;
    }
    for (const r of nextOther) {
      const k = r.key.trim();
      if (k && r.value.trim()) out[k] = r.value;
    }
    onChange(out);
  };

  const setNamed = (key: string, value: string): void => {
    flush({ ...values, [key]: value }, otherRows);
  };

  const addOther = (): void => {
    flush(values, [...otherRows, { id: ++rowSeq, key: '', value: '' }]);
  };

  const updateOther = (id: number, patch: Partial<Row>): void => {
    flush(
      values,
      otherRows.map((r) => (r.id === id ? { ...r, ...patch } : r)),
    );
  };

  const removeOther = (id: number): void => {
    flush(
      values,
      otherRows.filter((r) => r.id !== id),
    );
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground/70">
          MCP credentials
        </div>
        <span className="text-[10px] text-muted-foreground/60">
          written to <span className="font-mono">~/Library/Application Support/cflt-ai-app/mcp.env</span>
        </span>
      </div>

      {FIELD_GROUPS.map((group) => (
        <fieldset
          key={group.title}
          className="space-y-2 rounded border border-border/50 bg-muted/10 p-3"
        >
          <legend className="px-1 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
            {group.title}
          </legend>
          <p className="text-[10px] text-muted-foreground/70">{group.hint}</p>
          <div className="space-y-1.5">
            {group.fields.map((f) => (
              <label key={f.key} className="flex items-center gap-2">
                <span className="w-40 shrink-0 truncate text-[11px] text-muted-foreground">
                  {f.label}
                </span>
                <input
                  type={f.secret ? 'password' : 'text'}
                  placeholder={f.placeholder ?? ''}
                  value={values[f.key] ?? ''}
                  onChange={(e) => setNamed(f.key, e.target.value)}
                  spellCheck={false}
                  className="flex-1 rounded bg-muted px-2 py-1 font-mono text-[11px] text-foreground outline-none"
                />
              </label>
            ))}
          </div>
        </fieldset>
      ))}

      <fieldset className="space-y-2 rounded border border-border/50 bg-muted/10 p-3">
        <legend className="px-1 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
          Other
        </legend>
        <p className="text-[10px] text-muted-foreground/70">
          Arbitrary KEY=value pairs (e.g. <span className="font-mono">TFE_TOKEN</span> for the Terraform MCP).
        </p>
        {otherRows.map((r) => (
          <div key={r.id} className="flex items-center gap-1.5">
            <input
              type="text"
              placeholder="KEY"
              value={r.key}
              onChange={(e) => updateOther(r.id, { key: e.target.value })}
              spellCheck={false}
              className="w-48 rounded bg-muted px-2 py-1 font-mono text-[11px] uppercase text-foreground outline-none"
            />
            <span className="text-muted-foreground/50">=</span>
            <input
              type="password"
              placeholder="value"
              value={r.value}
              onChange={(e) => updateOther(r.id, { value: e.target.value })}
              spellCheck={false}
              className="flex-1 rounded bg-muted px-2 py-1 font-mono text-[11px] text-foreground outline-none"
            />
            <button
              type="button"
              onClick={() => removeOther(r.id)}
              aria-label="Remove"
              className="rounded p-1 text-muted-foreground/60 hover:bg-danger/15 hover:text-danger"
            >
              <Trash2 className="h-3 w-3" />
            </button>
          </div>
        ))}
        <button
          type="button"
          onClick={addOther}
          className="flex items-center gap-1 rounded px-2 py-0.5 text-[10px] uppercase tracking-wide text-muted-foreground hover:bg-muted hover:text-foreground"
        >
          <Plus className="h-3 w-3" /> add
        </button>
      </fieldset>

      <Hint>
        After saving, click <span className="font-mono">⌘⇧R</span> (or the ↻
        button in the titlebar) to re-probe MCP. The mcp-confluent dot turns
        green once the Cloud credentials authenticate.
      </Hint>
    </div>
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
