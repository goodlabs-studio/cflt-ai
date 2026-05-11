// User-tunable runtime settings persisted to {userData}/settings.json.
// Credential KEY=value pairs are also rendered to {userData}/mcp.env so
// mcp-confluent (which reads --env-file) can pick them up.

import { mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { app, ipcMain } from 'electron';
import type { UserConfig } from '@shared/types';

const DEFAULTS: UserConfig = {
  maxBudgetUsd: 2.0,
  defaultAskMode: 'ephemeral',
  defaultApplyProfile: 'read-only',
  defaultOverlay: '',
};

function settingsPath(): string {
  return join(app.getPath('userData'), 'settings.json');
}

export function mcpEnvFilePath(): string {
  return join(app.getPath('userData'), 'mcp.env');
}

let cached: UserConfig | null = null;

export function loadConfig(): UserConfig {
  if (cached) return cached;
  try {
    const raw = readFileSync(settingsPath(), 'utf-8');
    const parsed = JSON.parse(raw) as Partial<UserConfig>;
    cached = { ...DEFAULTS, ...parsed };
  } catch {
    cached = { ...DEFAULTS };
  }
  return cached;
}

function writeMcpEnvFile(vars: Record<string, string> | undefined): void {
  const path = mcpEnvFilePath();
  try {
    mkdirSync(dirname(path), { recursive: true });
    if (!vars || Object.keys(vars).length === 0) {
      writeFileSync(path, '', { mode: 0o600 });
      return;
    }
    const body = Object.entries(vars)
      .filter(([k]) => k.trim().length > 0)
      .map(([k, v]) => `${k.trim()}=${v}`)
      .join('\n');
    writeFileSync(path, body + '\n', { mode: 0o600 });
    console.log(`[cflt-ai] wrote ${Object.keys(vars).length} MCP env var(s) to ${path}`);
  } catch (err) {
    console.error('[cflt-ai] failed to write mcp env file:', err);
  }
}

function saveConfig(cfg: UserConfig): UserConfig {
  cached = cfg;
  try {
    mkdirSync(dirname(settingsPath()), { recursive: true });
    writeFileSync(settingsPath(), JSON.stringify(cfg, null, 2));
  } catch {
    /* read-only userData; settings won't persist but in-memory cache stays */
  }
  writeMcpEnvFile(cfg.mcpEnvVars);
  return cfg;
}

export function registerConfigHandlers(): void {
  // Materialize the env file from the cached config at boot so the very
  // first MCP probe sees a non-empty file.
  writeMcpEnvFile(loadConfig().mcpEnvVars);
  ipcMain.handle('config:get', async () => loadConfig());
  ipcMain.handle(
    'config:set',
    async (_e, patch: Partial<UserConfig>) => saveConfig({ ...loadConfig(), ...patch }),
  );
}
