// Parser for /review skill output. Extracts:
//   1. The intermediate ```yaml claims: ...``` block (REVW-01)
//   2. The ## Claim Validation markdown tables (per-claim verdicts)
// Merges both by claim ID into a unified ParsedReview shape the renderer
// can render as a chip-laden table.
//
// Tolerant of streaming partial input. parseReview() can be called with
// a growing string buffer; it returns a best-effort snapshot.

import type {
  ClaimCategory,
  ClaimVerdict,
  ParsedReview,
  ReviewClaim,
} from '@shared/types';

const VALID_CATEGORIES: ClaimCategory[] = [
  'config_value',
  'behavior_assertion',
  'architecture_choice',
  'metric_sla',
  'comparison',
];

const VALID_VERDICTS: ClaimVerdict[] = [
  'Confirmed',
  'Corrected',
  'Unverifiable',
];

export function parseReview(text: string): ParsedReview {
  const title = extractTitle(text);
  const { claims, complete: claimsComplete } = parseClaimsBlock(text);
  const validationByClaim = parseValidationTables(text);

  // Merge validation rows into claims by id
  for (const claim of claims) {
    const v = validationByClaim.get(claim.id);
    if (v) {
      claim.wikiSource = v.wiki;
      claim.mcpSource = v.mcp;
      claim.verdict = v.verdict;
    }
  }

  // If we saw validation rows for IDs we didn't capture in YAML (e.g.,
  // YAML was malformed but the table is fine), surface them as Pending
  // claims so they're not silently lost.
  for (const [id, v] of validationByClaim) {
    if (!claims.some((c) => c.id === id)) {
      claims.push({
        id,
        sourceFile: id.split('-')[0] ?? '',
        sourceSection: '',
        category: 'behavior_assertion',
        text: v.claimText ?? '(claim text not captured)',
        wikiSource: v.wiki,
        mcpSource: v.mcp,
        verdict: v.verdict,
      });
    }
  }

  return {
    title,
    claims,
    claimsComplete,
    validationComplete: validationByClaim.size > 0,
  };
}

function extractTitle(text: string): string {
  const m = /^#\s+(.+?)\s*$/m.exec(text);
  return m ? m[1].trim() : '';
}

// ─── Claims YAML block ─────────────────────────────────────────────────

const YAML_BLOCK_RE = /```yaml\s*\nclaims:\s*\n([\s\S]*?)```/m;
const YAML_BLOCK_OPEN_RE = /```yaml\s*\nclaims:\s*\n([\s\S]*)$/m;

interface ClaimsBlockResult {
  claims: ReviewClaim[];
  complete: boolean; // whether the closing ``` was seen
}

function parseClaimsBlock(text: string): ClaimsBlockResult {
  const closed = YAML_BLOCK_RE.exec(text);
  if (closed) {
    return { claims: parseClaimsYaml(closed[1]), complete: true };
  }
  const open = YAML_BLOCK_OPEN_RE.exec(text);
  if (open) {
    return { claims: parseClaimsYaml(open[1]), complete: false };
  }
  return { claims: [], complete: false };
}

/**
 * Parse the inner YAML body (after `claims:`). Avoids a YAML lib by
 * matching the constrained shape the skill produces:
 *   - id: "..."
 *     source_file: "..."
 *     source_section: "..."
 *     category: <bare identifier>
 *     text: "..."
 */
function parseClaimsYaml(body: string): ReviewClaim[] {
  const claims: ReviewClaim[] = [];
  // Split on lines starting with "  - id:" (each claim entry begins there).
  const entries = body.split(/^(?=\s*-\s+id:\s*)/m);
  for (const entry of entries) {
    if (!/-\s+id:/.test(entry)) continue;
    const id = takeField(entry, 'id');
    if (!id) continue;
    const category = (takeField(entry, 'category') ?? '') as ClaimCategory;
    claims.push({
      id,
      sourceFile: takeField(entry, 'source_file') ?? '',
      sourceSection: takeField(entry, 'source_section') ?? '',
      category: VALID_CATEGORIES.includes(category)
        ? category
        : 'behavior_assertion',
      text: takeField(entry, 'text') ?? '',
    });
  }
  return claims;
}

function takeField(entry: string, name: string): string | undefined {
  const re = new RegExp(`(?:^|\\n)\\s*(?:-\\s+)?${name}:\\s*(.*?)\\s*(?=\\n|$)`);
  const m = re.exec(entry);
  if (!m) return undefined;
  let val = m[1];
  // Strip surrounding quotes
  if (
    (val.startsWith('"') && val.endsWith('"')) ||
    (val.startsWith("'") && val.endsWith("'"))
  ) {
    val = val.slice(1, -1).replace(/\\"/g, '"').replace(/\\'/g, "'");
  }
  return val;
}

// ─── Validation tables ─────────────────────────────────────────────────
//
// The skill renders tables like:
//
//   | # | Claim | Wiki | MCP | Verdict |
//   |---|-------|------|-----|---------|
//   | deck-1 | text | art | src | Confirmed |
//
// Multiple tables can appear under different ### subsections. We collect
// rows from all of them.

interface ValidationRow {
  wiki: string;
  mcp: string;
  verdict: ClaimVerdict;
  claimText?: string;
}

const TABLE_HEADER_RE = /\|\s*#\s*\|\s*Claim\s*\|\s*Wiki\s*\|\s*MCP\s*\|\s*Verdict\s*\|/i;

function parseValidationTables(text: string): Map<string, ValidationRow> {
  const out = new Map<string, ValidationRow>();
  const lines = text.split('\n');
  let inTable = false;

  for (let i = 0; i < lines.length; i++) {
    if (TABLE_HEADER_RE.test(lines[i])) {
      // Skip the header and the |---|---|... separator.
      inTable = true;
      i += 1;
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
    if (cells.length < 5) continue;
    const [id, claimText, wiki, mcp, verdictRaw] = cells;
    const verdict = canonicalizeVerdict(verdictRaw);
    if (!verdict) continue;
    out.set(id, { wiki, mcp, verdict, claimText });
  }
  return out;
}

function canonicalizeVerdict(s: string): ClaimVerdict | null {
  const norm = s.trim();
  for (const v of VALID_VERDICTS) {
    if (v.toLowerCase() === norm.toLowerCase()) return v;
  }
  return null;
}
