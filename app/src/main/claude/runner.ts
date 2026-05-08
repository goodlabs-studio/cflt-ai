// Subprocess runner for `claude --print --output-format stream-json`.
// Wraps in `zsh -ilc` so user shell env (CONFLUENT_MCP_ENV_FILE, etc.) is
// inherited from ~/.zshrc, matching how skills behave when run interactively.

import { spawn, type ChildProcess } from 'node:child_process';
import { randomUUID } from 'node:crypto';
import type { WebContents } from 'electron';
import { getRepoRoot } from '../repo.js';
import { LineParser } from './parser.js';
import { acquire, classify, release } from '../concurrency.js';
import type { SkillRequest, StreamEvent, SkillResult } from '@shared/types';

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

const DEFAULT_MAX_BUDGET_USD = 2.0;
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
  const child = spawn('zsh', ['-ilc', cmd], {
    cwd: repoRoot,
    stdio: ['ignore', 'pipe', 'pipe'],
    env: { ...process.env },
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
 * Build the `claude` CLI command string for a given skill request.
 * The string is passed to `zsh -ilc`, so we shell-quote user input.
 */
function buildClaudeCommand(req: SkillRequest): string {
  const maxBudget = DEFAULT_MAX_BUDGET_USD;
  const maxTurns = DEFAULT_MAX_TURNS_BY_KIND[req.kind] ?? 20;
  const base = [
    'claude',
    '--print',
    '--output-format',
    'stream-json',
    '--verbose',
    `--max-turns ${maxTurns}`,
    `--max-budget-usd ${maxBudget}`,
  ];

  // Each skill request is invoked as a slash command. The user input is
  // appended as the prompt argument; quoting handles spaces/quotes.
  switch (req.kind) {
    case 'ask': {
      const args = [
        `--mode ${req.mode}`,
        req.forceRoute ? `--force-route ${req.forceRoute}` : '',
        shellQuote(req.query),
      ]
        .filter(Boolean)
        .join(' ');
      return `${base.join(' ')} ${shellQuote(`/ask ${args}`)}`;
    }
    case 'review': {
      const args = [
        req.output ? `--output ${req.output}` : '',
        req.overlay ? `--overlay ${shellQuote(req.overlay)}` : '',
        req.docPaths.map(shellQuote).join(' '),
      ]
        .filter(Boolean)
        .join(' ');
      return `${base.join(' ')} ${shellQuote(`/review ${args}`)}`;
    }
    case 'wiki:lint':
    case 'wiki:validate':
    case 'wiki:ingest':
    case 'wiki:evaluate':
    case 'wiki:recommend': {
      const cmd = req.kind.replace(':', ':');
      const args = req.args ?? '';
      return `${base.join(' ')} ${shellQuote(`/${cmd} ${args}`.trim())}`;
    }
    case 'dsp:plan': {
      const args = [
        req.overlay ? `--overlay ${shellQuote(req.overlay)}` : '',
        req.gateBypass?.length
          ? req.gateBypass.map((g) => `--gate-bypass ${g}`).join(' ')
          : '',
        shellQuote(req.request),
      ]
        .filter(Boolean)
        .join(' ');
      return `${base.join(' ')} ${shellQuote(`/dsp:plan ${args}`)}`;
    }
    case 'dsp:apply': {
      const args = [
        `--plan ${shellQuote(req.planPath)}`,
        `--profile ${req.profile}`,
        req.overlay ? `--overlay ${shellQuote(req.overlay)}` : '',
        req.operator ? `--operator ${shellQuote(req.operator)}` : '',
      ]
        .filter(Boolean)
        .join(' ');
      return `${base.join(' ')} ${shellQuote(`/dsp:apply ${args}`)}`;
    }
  }
}

/**
 * Single-quote the argument for zsh, escaping any embedded single quotes.
 * `foo 'bar'` becomes `'foo '\''bar'\'''`.
 */
function shellQuote(s: string): string {
  return `'${s.replace(/'/g, `'\\''`)}'`;
}
