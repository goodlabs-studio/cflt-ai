// Global concurrency guard. Lives in main; the renderer enqueues skill
// runs and the guard releases when the subprocess closes.
//
// Policy (Phase B.2):
//   - Mutating skills:    at most 1 active at a time
//   - Non-mutating skills: at most 3 active at a time
//
// Mutating means it writes durable artifacts that other concurrent runs
// would race on (wiki/_queue.md, wiki/activity/, outputs/, fsi-dsp state).
// Non-mutating is read-only inspection or speculative work that can be
// cancelled without consequence.

import type { BrowserWindow } from 'electron';
import type {
  ConcurrencyState,
  SkillClass,
  SkillRequest,
} from '@shared/types';

const MAX_MUTATING = 1;
const MAX_NON_MUTATING = 3;

interface QueuedRun {
  cls: SkillClass;
  resolve: () => void;
}

let mutatingActive = 0;
let nonMutatingActive = 0;
const queue: QueuedRun[] = [];

let snapshotListeners: Array<(s: ConcurrencyState) => void> = [];

export function classify(req: SkillRequest): SkillClass {
  switch (req.kind) {
    case 'dsp:apply':
    case 'wiki:ingest':
      return 'mutating';
    case 'review':
      // Review only mutates if it writes its report (default behavior).
      // We don't expose a "no-output" mode in B.2; treat as mutating to
      // be safe.
      return 'mutating';
    case 'ask':
      return req.mode === 'ephemeral' ? 'non-mutating' : 'mutating';
    case 'wiki:recommend':
    case 'wiki:evaluate':
      // Both write to wiki / outputs.
      return 'mutating';
    case 'wiki:lint':
    case 'wiki:validate':
    case 'dsp:plan':
      return 'non-mutating';
  }
}

/**
 * Acquire a slot for the given skill class. Resolves immediately if a slot
 * is free; otherwise resolves when one frees up. Caller MUST `release()`
 * exactly once when the run completes.
 */
export async function acquire(cls: SkillClass): Promise<void> {
  if (canStart(cls)) {
    grant(cls);
    return;
  }
  return new Promise<void>((resolve) => {
    queue.push({ cls, resolve });
    publish();
  });
}

export function release(cls: SkillClass): void {
  if (cls === 'mutating') mutatingActive = Math.max(0, mutatingActive - 1);
  else nonMutatingActive = Math.max(0, nonMutatingActive - 1);
  drain();
  publish();
}

function canStart(cls: SkillClass): boolean {
  return cls === 'mutating'
    ? mutatingActive < MAX_MUTATING
    : nonMutatingActive < MAX_NON_MUTATING;
}

function grant(cls: SkillClass): void {
  if (cls === 'mutating') mutatingActive += 1;
  else nonMutatingActive += 1;
  publish();
}

function drain(): void {
  // Pull from queue head while compatible slots free up. FIFO.
  while (queue.length > 0 && canStart(queue[0].cls)) {
    const next = queue.shift()!;
    grant(next.cls);
    next.resolve();
  }
}

export function snapshot(): ConcurrencyState {
  return {
    mutatingActive,
    nonMutatingActive,
    queueDepth: queue.length,
  };
}

export function subscribe(
  cb: (s: ConcurrencyState) => void,
): () => void {
  snapshotListeners.push(cb);
  cb(snapshot());
  return () => {
    snapshotListeners = snapshotListeners.filter((l) => l !== cb);
  };
}

function publish(): void {
  const s = snapshot();
  for (const l of snapshotListeners) l(s);
}

/**
 * Convenience: broadcast snapshot to all open windows. Called by
 * registerConcurrencyBroadcast() in main/index.ts.
 */
export function broadcastTo(windows: BrowserWindow[]): () => void {
  const send = (s: ConcurrencyState): void => {
    for (const w of windows) {
      if (!w.isDestroyed()) w.webContents.send('concurrency:state', s);
    }
  };
  return subscribe(send);
}
