// MCP IPC: out-of-band health probe via `claude mcp list`.
//
// `claude mcp list` runs each configured server's health check (stdio
// servers from .mcp.json are spawned ephemerally) and prints one line
// per server in the form:
//   <name>: <command-or-url> - <icon> <status-text>
// where icon is one of: ✓ Connected | ! Needs authentication | ✗ Failed
//
// Zero LLM cost. We only care about <name> and <status>.

import { spawn } from 'node:child_process';
import { ipcMain } from 'electron';
import { getRepoRoot } from '../repo.js';
import type { McpServerStatus } from '@shared/types';

const STATUS_RE =
  /^(.+?):\s.*?\s-\s(?:(✓\s*Connected)|(!\s*Needs authentication)|(✗\s*Failed[^\n]*))$/i;

export function parseMcpListOutput(stdout: string): McpServerStatus[] {
  const out: McpServerStatus[] = [];
  for (const raw of stdout.split('\n')) {
    const line = raw.trim();
    if (!line) continue;
    const m = STATUS_RE.exec(line);
    if (!m) continue;
    const name = m[1].trim();
    const status: McpServerStatus['status'] = m[2]
      ? 'connected'
      : m[3]
        ? 'needs-auth'
        : 'failed';
    out.push({ name, status });
  }
  return out;
}

export function probeMcpServers(): Promise<McpServerStatus[]> {
  return new Promise((resolve) => {
    const repoRoot = getRepoRoot();
    // Use login shell for env propagation (CONFLUENT_MCP_ENV_FILE etc).
    const child = spawn('zsh', ['-ilc', 'claude mcp list'], {
      cwd: repoRoot,
      stdio: ['ignore', 'pipe', 'pipe'],
      env: { ...process.env },
    });
    let stdout = '';
    child.stdout?.setEncoding('utf-8');
    child.stdout?.on('data', (c: string) => {
      stdout += c;
    });
    child.on('error', () => resolve([]));
    child.on('close', () => resolve(parseMcpListOutput(stdout)));
  });
}

export function registerMcpHandlers(): void {
  ipcMain.handle('mcp:health', async () => probeMcpServers());
}
