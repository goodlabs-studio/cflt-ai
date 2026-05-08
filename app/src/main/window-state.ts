// Persistent BrowserWindow bounds across launches.

import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { app, type BrowserWindow } from 'electron';

interface Bounds {
  x?: number;
  y?: number;
  width: number;
  height: number;
}

const DEFAULT_BOUNDS: Bounds = {
  width: 1280,
  height: 820,
};

function statePath(): string {
  return join(app.getPath('userData'), 'window-state.json');
}

export function loadWindowBounds(): Bounds {
  try {
    const raw = readFileSync(statePath(), 'utf-8');
    const parsed = JSON.parse(raw);
    return {
      x: typeof parsed.x === 'number' ? parsed.x : undefined,
      y: typeof parsed.y === 'number' ? parsed.y : undefined,
      width: typeof parsed.width === 'number' ? parsed.width : DEFAULT_BOUNDS.width,
      height: typeof parsed.height === 'number' ? parsed.height : DEFAULT_BOUNDS.height,
    };
  } catch {
    return DEFAULT_BOUNDS;
  }
}

/**
 * Wire save-on-close / save-on-resize for the window. Calls happen on
 * 'close', not 'closed', so window.getBounds() is still valid.
 */
export function attachWindowState(win: BrowserWindow): void {
  const save = (): void => {
    if (win.isDestroyed()) return;
    const bounds = win.getBounds();
    try {
      mkdirSync(dirname(statePath()), { recursive: true });
      writeFileSync(statePath(), JSON.stringify(bounds, null, 2));
    } catch {
      /* user-data unavailable; skip silently */
    }
  };
  win.on('close', save);
  win.on('resize', debounce(save, 500));
  win.on('move', debounce(save, 500));
}

function debounce<F extends (...args: unknown[]) => void>(fn: F, ms: number): F {
  let t: ReturnType<typeof setTimeout> | null = null;
  return ((...args: unknown[]) => {
    if (t) clearTimeout(t);
    t = setTimeout(() => fn(...args), ms);
  }) as F;
}
