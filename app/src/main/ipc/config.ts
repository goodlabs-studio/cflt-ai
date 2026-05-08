// User-tunable runtime settings persisted to {userData}/settings.json.

import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { app, ipcMain } from 'electron';
import type { UserConfig } from '@shared/types';

const DEFAULTS: UserConfig = {
  maxBudgetUsd: 2.0,
  defaultAskMode: 'ephemeral',
  defaultApplyProfile: 'read-only',
  defaultOverlay: '',
};

function path(): string {
  return join(app.getPath('userData'), 'settings.json');
}

let cached: UserConfig | null = null;

export function loadConfig(): UserConfig {
  if (cached) return cached;
  try {
    const raw = readFileSync(path(), 'utf-8');
    const parsed = JSON.parse(raw) as Partial<UserConfig>;
    cached = { ...DEFAULTS, ...parsed };
  } catch {
    cached = { ...DEFAULTS };
  }
  return cached;
}

function saveConfig(cfg: UserConfig): UserConfig {
  cached = cfg;
  try {
    mkdirSync(dirname(path()), { recursive: true });
    writeFileSync(path(), JSON.stringify(cfg, null, 2));
  } catch {
    /* read-only userData; settings won't persist but in-memory cache stays */
  }
  return cfg;
}

export function registerConfigHandlers(): void {
  ipcMain.handle('config:get', async () => loadConfig());
  ipcMain.handle(
    'config:set',
    async (_e, patch: Partial<UserConfig>) => saveConfig({ ...loadConfig(), ...patch }),
  );
}
