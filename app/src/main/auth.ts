// Detect how the Claude Code CLI is authenticated. Drives whether the
// renderer shows the per-run cost meta (API-key users see real charges;
// subscription users see no per-call billing, so the dollar figure is
// just noise).
//
// Detection order (first match wins):
//   1. ANTHROPIC_API_KEY env var set       → 'api-key'
//   2. ~/.claude/.credentials.json contains a top-level apiKey field → 'api-key'
//   3. Otherwise                            → 'oauth'
//
// We default to 'oauth' because the macOS keychain (where Claude.ai OAuth
// tokens land) is harder to probe synchronously and almost all Claude Code
// users are on a Pro/Max subscription. False positives ("oauth" when the
// user actually has API auth via a method we missed) only hide the cost
// number — which is the safer failure mode for a subscription-leaning UX.

import { existsSync, readFileSync } from 'node:fs';
import { homedir } from 'node:os';
import { join } from 'node:path';

export type AuthMode = 'oauth' | 'api-key';

let cached: AuthMode | null = null;

export function detectAuthMode(): AuthMode {
  if (cached !== null) return cached;

  if (process.env.ANTHROPIC_API_KEY && process.env.ANTHROPIC_API_KEY.trim()) {
    cached = 'api-key';
    return cached;
  }

  const credPath = join(homedir(), '.claude', '.credentials.json');
  if (existsSync(credPath)) {
    try {
      const raw = readFileSync(credPath, 'utf-8');
      const data = JSON.parse(raw) as Record<string, unknown>;
      if (typeof data['apiKey'] === 'string' && data['apiKey'].length > 0) {
        cached = 'api-key';
        return cached;
      }
    } catch {
      // Malformed file — fall through to default
    }
  }

  cached = 'oauth';
  return cached;
}
