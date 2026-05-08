// Generic python tool runner. Spawns `python3 tools/<name>.py [args...]`,
// streams stdout/stderr to the renderer (for streaming variants), and
// resolves with full stdout/stderr/exit code (for collect variants).
//
// Used by ipc/tool.ts to bridge wiki-lint, wiki-search, wiki-stats, and
// review-to-docx. No concurrency guard — these are local Python tools,
// not API-cost-bearing claude subprocesses.

import { spawn, type ChildProcess } from 'node:child_process';
import { randomUUID } from 'node:crypto';
import type { WebContents } from 'electron';
import { getRepoRoot } from '../repo.js';
import type { ToolOutputChunk } from '@shared/types';

interface ActiveToolRun {
  toolId: string;
  child: ChildProcess;
  webContents: WebContents | null;
}

const runs = new Map<string, ActiveToolRun>();

export interface CollectResult {
  exitCode: number;
  stdout: string;
  stderr: string;
}

/**
 * Spawn a python tool and collect full stdout/stderr/exit code. Suitable
 * for one-shot tools that produce a single result (wiki-search, wiki-stats,
 * review-to-docx).
 */
export function collectTool(
  script: string,
  args: string[] = [],
): Promise<CollectResult> {
  return new Promise((resolve, reject) => {
    const repoRoot = getRepoRoot();
    const child = spawn('python3', [`tools/${script}`, ...args], {
      cwd: repoRoot,
      stdio: ['ignore', 'pipe', 'pipe'],
      env: { ...process.env, PYTHONUNBUFFERED: '1' },
    });
    let stdout = '';
    let stderr = '';
    child.stdout?.setEncoding('utf-8');
    child.stderr?.setEncoding('utf-8');
    child.stdout?.on('data', (c: string) => {
      stdout += c;
    });
    child.stderr?.on('data', (c: string) => {
      stderr += c;
    });
    child.on('error', (err) => reject(err));
    child.on('close', (code) => {
      resolve({ exitCode: code ?? -1, stdout, stderr });
    });
  });
}

/**
 * Spawn a python tool and stream stdout/stderr chunks to webContents over
 * `tool:output` keyed by toolId. Returns toolId; renderer correlates via
 * the channel. Suitable for long-running tools (wiki-lint --full).
 */
export function streamTool(
  webContents: WebContents,
  script: string,
  args: string[] = [],
): string {
  const toolId = randomUUID();
  const repoRoot = getRepoRoot();
  const child = spawn('python3', [`tools/${script}`, ...args], {
    cwd: repoRoot,
    stdio: ['ignore', 'pipe', 'pipe'],
    env: { ...process.env, PYTHONUNBUFFERED: '1' },
  });
  runs.set(toolId, { toolId, child, webContents });

  const send = (chunk: ToolOutputChunk): void => {
    if (!webContents || webContents.isDestroyed()) return;
    webContents.send('tool:output', toolId, chunk);
  };

  child.stdout?.setEncoding('utf-8');
  child.stderr?.setEncoding('utf-8');
  child.stdout?.on('data', (c: string) => send({ kind: 'stdout', text: c }));
  child.stderr?.on('data', (c: string) => send({ kind: 'stderr', text: c }));
  child.on('error', (err) =>
    send({ kind: 'stderr', text: `\n[runner error] ${err.message}\n` }),
  );
  child.on('close', (code) => {
    send({ kind: 'exit', code: code ?? -1 });
    runs.delete(toolId);
  });

  return toolId;
}

export function cancelTool(toolId: string): boolean {
  const run = runs.get(toolId);
  if (!run) return false;
  try {
    run.child.kill('SIGTERM');
  } catch {
    /* already dead */
  }
  setTimeout(() => {
    if (runs.has(toolId)) {
      try {
        run.child.kill('SIGKILL');
      } catch {
        /* already dead */
      }
    }
  }, 2000);
  return true;
}

export function disposeAllTools(): void {
  for (const [id] of runs) cancelTool(id);
}
