// Parse a saved /dsp:plan markdown file into the shape the apply
// confirmation modal needs.  Reuses parsePlan() for gate + artifact
// extraction, then layers on Arguments and Canon Compliance sections
// that aren't streaming-relevant.

import type { PlanSummary } from '@shared/types';
import { parsePlan } from './plan-parse';

const ARGS_BLOCK_RE = /##\s+Arguments\s*\n([\s\S]*?)(?=\n##\s|\n```|$)/i;
const CANON_BLOCK_RE = /##\s+Canon Compliance\s*\n([\s\S]*?)(?=\n##\s|$)/i;
const PROVENANCE_RE = /^Canon stack:.*$/m;
const ARG_LINE_RE = /^\s*[-*]\s*\*\*([^*]+):\*\*\s*(.+)$/;

export function parsePlanFile(slug: string, path: string, body: string): PlanSummary {
  const planParse = parsePlan(body);
  const argsMatch = ARGS_BLOCK_RE.exec(body);
  const canonMatch = CANON_BLOCK_RE.exec(body);
  const provMatch = PROVENANCE_RE.exec(body);
  const dateMatch = /(\d{4}-\d{2}-\d{2})/.exec(slug);

  const args: Array<{ key: string; value: string }> = [];
  if (argsMatch) {
    for (const line of argsMatch[1].split('\n')) {
      const m = ARG_LINE_RE.exec(line);
      if (m) args.push({ key: m[1].trim(), value: m[2].trim() });
    }
  }

  return {
    slug,
    path,
    date: dateMatch?.[1],
    artifact: planParse.artifact,
    arguments: args.length > 0 ? args : undefined,
    gates: planParse.gates,
    canonCompliance: canonMatch ? canonMatch[1].trim() : undefined,
    provenance: provMatch ? provMatch[0] : undefined,
  };
}
