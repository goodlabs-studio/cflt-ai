// Parser for /dsp:plan skill output. Extracts gate progress and the
// selected artifact from streaming markdown so the renderer can animate
// the 4-gate chain and surface the artifact preview the moment it lands.
//
// Sources of truth in the stream:
//   1. "Gate Results" markdown table:
//        | gate | status | detail |
//        |---|---|---|
//        | canon_compliance | pass | ... |
//   2. Provenance footer:  "Gate results: canon_compliance:pass, ..."
//   3. Selected Artifact section:
//        ## Selected Artifact
//        **ID:** module/topic
//        **Path:** ...
//        **Description:** ...
//
// Parser is tolerant: a gate not yet seen is `pending`; a gate mentioned
// in a streaming line that hasn't completed its row is `running`.

import {
  GATE_NAMES,
  type GateInfo,
  type GateName,
  type GateState,
  type ParsedPlan,
  type SelectedArtifact,
} from '@shared/types';

const GATE_NAME_SET = new Set<string>(GATE_NAMES);

const TABLE_HEADER_RE = /\|\s*gate\s*\|\s*status\s*\|\s*detail\s*\|/i;
const TABLE_SEPARATOR_RE = /^\s*\|\s*-+\s*\|/;
const FOOTER_LINE_RE = /Gate results:\s*([^\n|]+)/i;
const ARTIFACT_HEADING_RE = /^##\s+Selected Artifact\s*$/im;
const ARTIFACT_BLOCK_RE =
  /##\s+Selected Artifact\s*\n([\s\S]*?)(?=\n##\s|\n```|$)/i;

/**
 * Best-effort snapshot of plan progress. Safe to call repeatedly with
 * a growing buffer.
 */
export function parsePlan(text: string): ParsedPlan {
  const tableGates = parseGateTable(text);
  const footerGates = parseFooterGates(text);

  const gates: GateInfo[] = GATE_NAMES.map<GateInfo>((name) => {
    // Prefer table state (richer detail) over footer state.
    return tableGates.get(name) ?? footerGates.get(name) ?? { name, state: 'pending' };
  });

  // Mark "running" heuristically: if no terminal state yet, but the gate
  // name has been mentioned in the stream after the most recent gate that
  // *does* have a terminal state, treat it as running. This makes the UI
  // animate as text streams in, before the table closes.
  applyRunningHeuristic(gates, text);

  const artifact = parseSelectedArtifact(text);
  const footerMatch = FOOTER_LINE_RE.exec(text);

  return {
    gates,
    gatesComplete: tableGates.size === GATE_NAMES.length,
    artifact,
    footerGateLine: footerMatch ? footerMatch[1].trim() : undefined,
  };
}

// ─── gate-results table ────────────────────────────────────────────────

function parseGateTable(text: string): Map<GateName, GateInfo> {
  const result = new Map<GateName, GateInfo>();
  const lines = text.split('\n');
  let inTable = false;
  for (let i = 0; i < lines.length; i++) {
    if (TABLE_HEADER_RE.test(lines[i])) {
      inTable = true;
      // skip the |---| separator if present
      if (i + 1 < lines.length && TABLE_SEPARATOR_RE.test(lines[i + 1])) i += 1;
      continue;
    }
    if (!inTable) continue;
    const line = lines[i].trim();
    if (!line.startsWith('|')) {
      inTable = false;
      continue;
    }
    const cells = line
      .replace(/^\|/, '')
      .replace(/\|$/, '')
      .split('|')
      .map((c) => c.trim());
    if (cells.length < 3) continue;
    const [gateRawRaw, statusRaw, detail] = cells;
    // Planner sometimes prefixes the gate name with a step number: "1. canon_compliance".
    // Strip leading "N. " or "N) " before the set lookup.
    const gateRaw = gateRawRaw.replace(/^\s*\d+\s*[.)]\s*/, '');
    if (!GATE_NAME_SET.has(gateRaw)) continue;
    const state = canonicalizeStatus(statusRaw);
    if (!state) continue;
    const evidence = cells
      .slice(3)
      .map((c) => c.trim())
      .filter(Boolean);
    result.set(gateRaw as GateName, {
      name: gateRaw as GateName,
      state,
      detail: detail || undefined,
      evidence: evidence.length > 0 ? evidence : undefined,
    });
  }
  return result;
}

function parseFooterGates(text: string): Map<GateName, GateInfo> {
  const m = FOOTER_LINE_RE.exec(text);
  const out = new Map<GateName, GateInfo>();
  if (!m) return out;
  for (const pair of m[1].split(',').map((p) => p.trim())) {
    const [gate, status] = pair.split(':').map((p) => p.trim());
    if (!GATE_NAME_SET.has(gate)) continue;
    const state = canonicalizeStatus(status);
    if (!state) continue;
    out.set(gate as GateName, { name: gate as GateName, state });
  }
  return out;
}

function canonicalizeStatus(s: string): GateState | null {
  const norm = s.toLowerCase().trim();
  if (norm === 'pass' || norm === 'passed') return 'pass';
  if (norm === 'fail' || norm === 'failed') return 'fail';
  if (norm === 'skip' || norm === 'skipped') return 'skipped';
  return null;
}

/**
 * If a gate is still `pending` but the stream mentions its name after the
 * last gate that's already terminal, mark it `running`. Cosmetic; helps
 * the chain animate as the model emits text leading up to the table.
 */
function applyRunningHeuristic(gates: GateInfo[], text: string): void {
  const lastTerminalIdx = lastIndex(gates, (g) => g.state !== 'pending');
  for (let i = 0; i < gates.length; i++) {
    const g = gates[i];
    if (g.state !== 'pending') continue;
    // Allow the next pending gate after the last terminal one to claim 'running'
    // if its name shows up anywhere in the stream past the previous terminal gate.
    if (i !== lastTerminalIdx + 1) continue;
    if (text.includes(g.name)) {
      g.state = 'running';
    }
    break;
  }
}

function lastIndex<T>(arr: T[], pred: (x: T) => boolean): number {
  for (let i = arr.length - 1; i >= 0; i--) {
    if (pred(arr[i])) return i;
  }
  return -1;
}

// ─── selected artifact ─────────────────────────────────────────────────

function parseSelectedArtifact(text: string): SelectedArtifact | undefined {
  if (!ARTIFACT_HEADING_RE.test(text)) return undefined;
  const block = ARTIFACT_BLOCK_RE.exec(text);
  if (!block) return undefined;
  const body = block[1];
  // Two forms in the wild:
  //   (1) Bold field:  **ID:** module/topic
  //   (2) 2-col table: | Artifact ID | `scenario/cc-gcp` |
  const id =
    takeBoldField(body, 'ID') ??
    takeBoldField(body, 'Id') ??
    takeTableField(body, /^artifact\s+id$/i);
  if (!id) return undefined;
  return {
    id,
    path: takeBoldField(body, 'Path') ?? takeTableField(body, /^path$/i),
    description:
      takeBoldField(body, 'Description') ??
      takeTableField(body, /^description$/i),
  };
}

function takeBoldField(body: string, name: string): string | undefined {
  const re = new RegExp(`\\*\\*${name}:\\*\\*\\s*\`?([^\`\\n]+)\`?\\s*$`, 'mi');
  const m = re.exec(body);
  return m ? m[1].trim() : undefined;
}

// Pull a value from a 2-column markdown table whose first column matches
// `keyRe`. Strips backtick wrappers from the value.
function takeTableField(body: string, keyRe: RegExp): string | undefined {
  for (const raw of body.split('\n')) {
    const line = raw.trim();
    if (!line.startsWith('|')) continue;
    const cells = line
      .replace(/^\|/, '')
      .replace(/\|$/, '')
      .split('|')
      .map((c) => c.trim());
    if (cells.length < 2) continue;
    if (keyRe.test(cells[0])) {
      return cells[1].replace(/^`/, '').replace(/`$/, '').trim() || undefined;
    }
  }
  return undefined;
}
