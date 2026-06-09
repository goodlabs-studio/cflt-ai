// Stream-json normalizer for `claude --output-format stream-json --verbose`
// (claude 2.1.131 schema baseline).
//
// Input: raw JSON-line objects from stdout.
// Output: typed StreamEvent discriminated union.
//
// Design notes:
// - Unknown raw event types fall through to {type:'raw'} so the UI can
//   degrade on CLI drift instead of crashing.
// - `[ROUTE: <route>]` markers in assistant text deltas are synthesized
//   into typed `route` events (per .claude/commands/ask.md:38,100).

import type {
  ClaudeRoute,
  InitInfo,
  McpServerStatus,
  StreamEvent,
} from '@shared/types';

const ROUTE_RE = /\[ROUTE:\s*(wiki(?:-only)?|mcp|wiki\+MCP|deep)\s*\]/i;

/**
 * Parse one raw stream-json line into zero or more typed events.
 * Multi-yield is needed because a single assistant message may carry both
 * an assistant_text event and a synthesized route event.
 */
export function parseLine(raw: unknown): StreamEvent[] {
  if (!isObject(raw) || typeof raw['type'] !== 'string') {
    return [{ type: 'raw', raw: (raw as Record<string, unknown>) ?? {} }];
  }

  const type = raw['type'] as string;

  // ── system events: init + hooks ──────────────────────────────────────
  if (type === 'system') {
    const subtype = (raw['subtype'] as string) ?? 'unknown';
    if (subtype === 'init') {
      return [{ type: 'init', info: parseInit(raw) }];
    }
    return [
      {
        type: 'system',
        subtype,
        data: raw as Record<string, unknown>,
      },
    ];
  }

  // ── assistant message: extract text + tool_use + route ───────────────
  if (type === 'assistant') {
    return parseAssistant(raw);
  }

  // ── user message: tool_result wrapper ────────────────────────────────
  if (type === 'user') {
    return parseUser(raw);
  }

  // ── rate limit ───────────────────────────────────────────────────────
  if (type === 'rate_limit_event') {
    const info = (raw['rate_limit_info'] as Record<string, unknown>) ?? {};
    return [
      {
        type: 'rate_limit',
        info: {
          status: (info['status'] as string) ?? 'unknown',
          resetsAt: typeof info['resetsAt'] === 'number' ? (info['resetsAt'] as number) : undefined,
          isUsingOverage: info['isUsingOverage'] === true,
        },
      },
    ];
  }

  // ── final result ─────────────────────────────────────────────────────
  if (type === 'result') {
    return [
      {
        type: 'result',
        result: {
          success:
            raw['subtype'] === 'success' && raw['is_error'] !== true,
          text: typeof raw['result'] === 'string' ? (raw['result'] as string) : '',
          durationMs:
            typeof raw['duration_ms'] === 'number' ? (raw['duration_ms'] as number) : 0,
          costUsd:
            typeof raw['total_cost_usd'] === 'number'
              ? (raw['total_cost_usd'] as number)
              : 0,
          inputTokens:
            isObject(raw['usage']) && typeof raw['usage']['input_tokens'] === 'number'
              ? (raw['usage']['input_tokens'] as number)
              : 0,
          outputTokens:
            isObject(raw['usage']) && typeof raw['usage']['output_tokens'] === 'number'
              ? (raw['usage']['output_tokens'] as number)
              : 0,
          sessionId:
            typeof raw['session_id'] === 'string'
              ? (raw['session_id'] as string)
              : undefined,
        },
      },
    ];
  }

  return [{ type: 'raw', raw: raw as Record<string, unknown> }];
}

function parseInit(raw: Record<string, unknown>): InitInfo {
  const mcpServersRaw = Array.isArray(raw['mcp_servers']) ? raw['mcp_servers'] : [];
  const mcpServers: McpServerStatus[] = mcpServersRaw
    .filter(isObject)
    .map((s) => ({
      name: typeof s['name'] === 'string' ? (s['name'] as string) : 'unknown',
      status: normalizeMcpStatus(s['status']),
    }));
  return {
    cwd: typeof raw['cwd'] === 'string' ? (raw['cwd'] as string) : '',
    model: typeof raw['model'] === 'string' ? (raw['model'] as string) : '',
    tools: Array.isArray(raw['tools']) ? (raw['tools'] as string[]) : [],
    mcpServers,
    sessionId:
      typeof raw['session_id'] === 'string' ? (raw['session_id'] as string) : '',
  };
}

function normalizeMcpStatus(s: unknown): McpServerStatus['status'] {
  // `pending` shows up in headless --print init snapshots: slow npx/uvx stdio
  // servers are still mid-handshake when the init event fires. They connect a
  // beat later, so it must not be flattened to `unknown` (which reads as down).
  if (
    s === 'connected' ||
    s === 'failed' ||
    s === 'needs-auth' ||
    s === 'pending'
  )
    return s;
  return 'unknown';
}

function parseAssistant(raw: Record<string, unknown>): StreamEvent[] {
  const message = raw['message'];
  if (!isObject(message)) return [{ type: 'raw', raw }];
  const messageId = typeof message['id'] === 'string' ? (message['id'] as string) : '';
  const content = Array.isArray(message['content']) ? message['content'] : [];

  const events: StreamEvent[] = [];
  for (const block of content) {
    if (!isObject(block)) continue;
    const blockType = block['type'];
    if (blockType === 'text') {
      const text = typeof block['text'] === 'string' ? (block['text'] as string) : '';
      if (text) {
        events.push({ type: 'assistant_text', text, messageId });
        // Synthesize route event from text marker
        const m = ROUTE_RE.exec(text);
        if (m) {
          const route = canonicalizeRoute(m[1]);
          if (route) events.push({ type: 'route', route });
        }
      }
    } else if (blockType === 'tool_use') {
      events.push({
        type: 'tool_use',
        tool: {
          id: typeof block['id'] === 'string' ? (block['id'] as string) : '',
          name: typeof block['name'] === 'string' ? (block['name'] as string) : 'unknown',
          input: block['input'],
        },
      });
    }
  }
  if (events.length === 0) return [{ type: 'raw', raw }];
  return events;
}

function parseUser(raw: Record<string, unknown>): StreamEvent[] {
  const message = raw['message'];
  if (!isObject(message)) return [{ type: 'raw', raw }];
  const content = Array.isArray(message['content']) ? message['content'] : [];

  const events: StreamEvent[] = [];
  for (const block of content) {
    if (!isObject(block)) continue;
    if (block['type'] === 'tool_result') {
      events.push({
        type: 'tool_result',
        result: {
          toolUseId:
            typeof block['tool_use_id'] === 'string'
              ? (block['tool_use_id'] as string)
              : '',
          output: block['content'],
          isError: block['is_error'] === true,
        },
      });
    }
  }
  if (events.length === 0) return [{ type: 'raw', raw }];
  return events;
}

function canonicalizeRoute(s: string): ClaudeRoute | null {
  const norm = s.toLowerCase();
  if (norm === 'wiki' || norm === 'wiki-only') return 'wiki';
  if (norm === 'mcp' || norm === 'wiki+mcp') return 'mcp';
  if (norm === 'deep') return 'deep';
  return null;
}

function isObject(v: unknown): v is Record<string, unknown> {
  return typeof v === 'object' && v !== null && !Array.isArray(v);
}

/**
 * Stateful line buffer. Accepts arbitrary chunks (which may split across
 * line boundaries) and yields one parsed StreamEvent at a time.
 */
export class LineParser {
  private buffer = '';

  push(chunk: string): StreamEvent[] {
    this.buffer += chunk;
    const out: StreamEvent[] = [];
    let nl: number;
    while ((nl = this.buffer.indexOf('\n')) !== -1) {
      const line = this.buffer.slice(0, nl).trim();
      this.buffer = this.buffer.slice(nl + 1);
      if (!line) continue;
      let parsed: unknown;
      try {
        parsed = JSON.parse(line);
      } catch {
        out.push({ type: 'error', message: `Invalid JSON line: ${line.slice(0, 200)}`, recoverable: true });
        continue;
      }
      out.push(...parseLine(parsed));
    }
    return out;
  }

  flush(): StreamEvent[] {
    const remainder = this.buffer.trim();
    this.buffer = '';
    if (!remainder) return [];
    try {
      const parsed = JSON.parse(remainder);
      return parseLine(parsed);
    } catch {
      return [{ type: 'error', message: `Trailing partial line: ${remainder.slice(0, 200)}`, recoverable: true }];
    }
  }
}
