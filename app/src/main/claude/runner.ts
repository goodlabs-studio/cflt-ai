// Subprocess runner for `claude --print --output-format stream-json`.
// Wraps in `zsh -ilc` so user shell env (CONFLUENT_MCP_ENV_FILE, etc.) is
// inherited from ~/.zshrc, matching how skills behave when run interactively.

import { spawn, type ChildProcess } from 'node:child_process';
import { randomUUID } from 'node:crypto';
import type { WebContents } from 'electron';
import { getRepoRoot } from '../repo.js';
import { LineParser } from './parser.js';
import { acquire, classify, release } from '../concurrency.js';
import { loadConfig, mcpEnvFilePath } from '../ipc/config.js';
import type { SkillRequest, StreamEvent, SkillResult } from '@shared/types';

// Subprocess env = parent env + user-managed MCP vars + auto-set
// CONFLUENT_MCP_ENV_FILE pointing at the managed file. Both surfaces
// are populated so any consumer (mcp-confluent reads --env-file; some
// tools read raw env) is covered.
function skillEnv(): NodeJS.ProcessEnv {
  const cfg = loadConfig();
  const env: NodeJS.ProcessEnv = { ...process.env };
  if (cfg.mcpEnvVars) {
    for (const [k, v] of Object.entries(cfg.mcpEnvVars)) {
      if (k.trim()) env[k.trim()] = v;
    }
  }
  if (!env['CONFLUENT_MCP_ENV_FILE']) {
    env['CONFLUENT_MCP_ENV_FILE'] = mcpEnvFilePath();
  }
  return env;
}

interface ActiveSession {
  sessionId: string;
  child: ChildProcess | null;     // null while queued waiting for a slot
  webContents: WebContents | null;
  pendingResult: Partial<SkillResult> | null;
  cancelled: boolean;
  released: boolean;
  cls: ReturnType<typeof classify>;
}

const sessions = new Map<string, ActiveSession>();

const DEFAULT_MAX_TURNS_BY_KIND: Record<string, number> = {
  ask: 10,
  review: 30,
  'wiki:lint': 5,
  'wiki:validate': 30,
  'wiki:ingest': 30,
  'wiki:evaluate': 30,
  'wiki:recommend': 30,
  'dsp:plan': 20,
  'dsp:apply': 30,
};

/** Run a skill request. Returns the sessionId immediately; events stream
 * to webContents until the subprocess exits or is cancelled. May queue
 * behind the concurrency guard before spawning. */
export function startRun(
  webContents: WebContents,
  req: SkillRequest,
): string {
  const sessionId = randomUUID();
  const cls = classify(req);
  const session: ActiveSession = {
    sessionId,
    child: null,
    webContents,
    pendingResult: null,
    cancelled: false,
    released: false,
    cls,
  };
  sessions.set(sessionId, session);

  const send = (ev: StreamEvent): void => {
    if (!session.webContents || session.webContents.isDestroyed()) return;
    session.webContents.send('skill:event', sessionId, ev);
    if (ev.type === 'result') session.pendingResult = ev.result;
  };

  // Acquire concurrency slot before spawning. acquire() resolves
  // immediately if a slot is free, or later when one frees up.
  acquire(cls)
    .then(() => {
      if (session.cancelled) {
        // Cancelled while queued — release the slot we just acquired.
        if (!session.released) {
          release(cls);
          session.released = true;
        }
        send({
          type: 'result',
          result: blankResult(false),
        });
        cleanup(sessionId);
        return;
      }
      spawnAndWire(session, req, send);
    })
    .catch((err: Error) => {
      send({ type: 'error', message: `concurrency guard failed: ${err.message}` });
      send({ type: 'result', result: blankResult(false) });
      cleanup(sessionId);
    });

  return sessionId;
}

function spawnAndWire(
  session: ActiveSession,
  req: SkillRequest,
  send: (ev: StreamEvent) => void,
): void {
  const repoRoot = getRepoRoot();
  const cmd = buildClaudeCommand(req);

  // -i (login shell) so ~/.zshrc env propagates; -l ensures profile too.
  // stdin is closed (text input mode) so claude auto-executes its own
  // tools. F.1's stream-json input experiment was reverted — in that mode
  // claude does NOT auto-execute tools (including MCP, Bash, Read), it
  // expects the orchestrator to feed back tool_result for every tool_use,
  // which our runner does not (and should not — that's claude's job).
  const child = spawn('zsh', ['-ilc', cmd], {
    cwd: repoRoot,
    stdio: ['ignore', 'pipe', 'pipe'],
    env: skillEnv(),
  });
  session.child = child;

  const parser = new LineParser();

  child.stdout?.setEncoding('utf-8');
  child.stdout?.on('data', (chunk: string) => {
    for (const ev of parser.push(chunk)) send(ev);
  });

  child.stderr?.setEncoding('utf-8');
  let stderrBuf = '';
  child.stderr?.on('data', (chunk: string) => {
    stderrBuf += chunk;
    if (stderrBuf.length > 4096) stderrBuf = stderrBuf.slice(-4096);
  });

  child.on('error', (err) => {
    send({ type: 'error', message: `Failed to spawn claude: ${err.message}` });
    cleanup(session.sessionId);
  });

  child.on('close', (code) => {
    for (const ev of parser.flush()) send(ev);
    if (!session.pendingResult) {
      const message =
        code === 0
          ? 'subprocess exited without a result event'
          : `subprocess exited with code ${code}${stderrBuf ? `: ${stderrBuf.trim().slice(-400)}` : ''}`;
      send({ type: 'error', message });
      send({ type: 'result', result: blankResult(code === 0) });
    }
    cleanup(session.sessionId);
  });
}

function blankResult(success: boolean): SkillResult {
  return {
    success,
    text: '',
    durationMs: 0,
    costUsd: 0,
    inputTokens: 0,
    outputTokens: 0,
  };
}

export function cancel(sessionId: string): boolean {
  const session = sessions.get(sessionId);
  if (!session) return false;
  session.cancelled = true;
  if (!session.child) {
    // Still queued. cleanup happens when acquire() resolves.
    return true;
  }
  try {
    session.child.kill('SIGTERM');
  } catch {
    /* already dead */
  }
  setTimeout(() => {
    if (sessions.has(sessionId) && session.child) {
      try {
        session.child.kill('SIGKILL');
      } catch {
        /* already dead */
      }
    }
  }, 2000);
  return true;
}

export function disposeAll(): void {
  for (const [id] of sessions) cancel(id);
}

function cleanup(sessionId: string): void {
  const session = sessions.get(sessionId);
  if (session && !session.released) {
    release(session.cls);
    session.released = true;
  }
  sessions.delete(sessionId);
}

/**
 * Build the full `claude` CLI command string for `zsh -ilc`. Text-input
 * mode — the prompt is shell-quoted and appended as the final argv.
 */
function buildClaudeCommand(req: SkillRequest): string {
  const maxBudget = loadConfig().maxBudgetUsd;
  const maxTurns = DEFAULT_MAX_TURNS_BY_KIND[req.kind] ?? 20;
  const base = [
    'claude',
    '--print',
    '--output-format',
    'stream-json',
    '--verbose',
    `--max-turns ${maxTurns}`,
    `--max-budget-usd ${maxBudget}`,
  ].join(' ');
  return `${base} ${shellQuote(buildPrompt(req))}`;
}

// Single-quote arg for zsh; escapes embedded single quotes.
function shellQuote(s: string): string {
  return `'${s.replace(/'/g, `'\\''`)}'`;
}

function buildPrompt(req: SkillRequest): string {
  switch (req.kind) {
    case 'ask': {
      const flags = [
        `--mode ${req.mode}`,
        req.forceRoute ? `--force-route ${req.forceRoute}` : '',
      ]
        .filter(Boolean)
        .join(' ');
      return `/ask ${flags} ${req.query}`.trim();
    }
    case 'review': {
      const flags = [
        req.output ? `--output ${req.output}` : '',
        req.overlay ? `--overlay ${req.overlay}` : '',
      ]
        .filter(Boolean)
        .join(' ');
      const paths = req.docPaths.join(' ');
      return `/review ${flags} ${paths}`.trim();
    }
    case 'wiki:lint':
    case 'wiki:validate':
    case 'wiki:ingest':
    case 'wiki:evaluate':
    case 'wiki:recommend':
      return `/${req.kind} ${req.args ?? ''}`.trim();
    case 'dsp:plan': {
      // Slash command is `/dsp-plan` (from filename `commands/dsp-plan.md`).
      // The kind keeps the colon for IPC-payload readability.
      const flags = [
        req.overlay ? `--overlay ${req.overlay}` : '',
        req.gateBypass?.length
          ? req.gateBypass.map((g) => `--gate-bypass ${g}`).join(' ')
          : '',
      ]
        .filter(Boolean)
        .join(' ');
      return `/dsp-plan ${flags} ${req.request}`.trim();
    }
    case 'dsp:apply': {
      // --reason is the only flag whose value can contain spaces or quotes,
      // so it gets its own escape. Everything else is bare tokens or paths.
      const reasonArg = req.reason
        ? `--reason "${req.reason.replace(/"/g, '\\"')}"`
        : '';
      const flags = [
        `--plan ${req.planPath}`,
        `--profile ${req.profile}`,
        req.overlay ? `--overlay ${req.overlay}` : '',
        req.operator ? `--operator ${req.operator}` : '',
        req.preConfirmed ? '--pre-confirmed' : '',
        reasonArg,
      ]
        .filter(Boolean)
        .join(' ');
      // Slash command is `/dsp-apply` (from filename `commands/dsp-apply.md`).
      return `/dsp-apply ${flags}`;
    }
  }
}
