// Skill IPC: connects the skill subprocess runner to the renderer.
// `skill:run` returns a sessionId; events are pushed via `skill:event`.

import { existsSync, readFileSync, readdirSync } from 'node:fs';
import { ipcMain } from 'electron';
import { resolveInRepo } from '../repo.js';
import { startRun, cancel, respondToTool, disposeAll } from '../claude/runner.js';
import type { Profile, SkillRequest } from '@shared/types';

function listProfiles(): Profile[] {
  const dir = 'tools/profiles';
  let abs: string;
  try {
    abs = resolveInRepo(dir);
  } catch {
    return [];
  }
  if (!existsSync(abs)) return [];
  return readdirSync(abs)
    .filter((f) => f.endsWith('.json') && f !== 'tool_classification.json')
    .sort()
    .map<Profile>((f) => {
      const path = `${dir}/${f}`;
      try {
        const raw = JSON.parse(readFileSync(resolveInRepo(path), 'utf-8'));
        return {
          name: typeof raw.name === 'string' ? raw.name : f.replace(/\.json$/, ''),
          allowedOperations: Array.isArray(raw.allowed_operations)
            ? raw.allowed_operations
            : [],
          description: typeof raw.description === 'string' ? raw.description : undefined,
        };
      } catch {
        return { name: f.replace(/\.json$/, ''), allowedOperations: [] };
      }
    });
}

export function registerSkillHandlers(): void {
  ipcMain.handle('skill:run', async (e, req: SkillRequest) => {
    return startRun(e.sender, req);
  });
  ipcMain.handle('skill:cancel', async (_e, sessionId: string) => {
    return cancel(sessionId);
  });
  ipcMain.handle(
    'skill:respond',
    async (_e, sessionId: string, toolUseId: string, content: string) =>
      respondToTool(sessionId, toolUseId, content),
  );
  ipcMain.handle('skill:listProfiles', async () => listProfiles());
}

export { disposeAll as disposeSkillSubprocesses };
