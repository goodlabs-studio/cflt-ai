# Writing rules for client documentation

These rules apply to every document, deck or Markdown file produced in this repo for a client or a teammate. All three are written in the same senior-architect voice (§1). They come from a GoodLabs solution design and deck delivered in November 2026, which read like an architect wrote them, not a model. Formatting lives in `DESIGN.md` §11. This file covers the words.

## 0. Which output to produce

| Request | Output |
|---|---|
| "documentation", "a doc", "write this up", "design doc", "proposal", "runbook" (no format named) | A single `.md` first pass, per §4. It is the review copy and costs far fewer tokens than a .docx |
| "make it a Word doc", "docx", "Word" (usually after the .md is reviewed) | A `.docx` converted from the reviewed `.md` with `tools/md2docx/md2docx.py`, which applies `DESIGN.md` §11.1. No PDF: the user exports it from Word |
| "deck", "slides", "presentation", "PowerPoint" | A `.pptx` built to `DESIGN.md` §11.2 |
| Both, or "doc and deck" | A matched pair (`DESIGN.md` §11.4) |
| "Markdown", ".md", "md version" | Same as the first pass: a single `.md` file only. No .docx, no artifact, no HTML. Follow §4 below |

Build a .docx by converting the reviewed `.md` with `tools/md2docx/md2docx.py` (pandoc). Don't hand-build one with the `anthropic-skills:docx` skill. Build a .pptx with the `anthropic-skills:pptx` skill. A spec in `DESIGN.md` §11 overrides any default in that skill. Write into the engagement's own folder (e.g. `~/GoodLabs/<Client>/`) or `outputs/`. Client material never goes into `wiki/`, and no client name goes into a committed file.

## 1. Voice: the senior architect, in every format

Every .docx, .pptx and .md is written in one voice: the senior streaming architect who owns the design and has run it in production. That architect explains a decision to people who will operate it. They're calm, specific and plain, and they never sell. Only the format changes; the author doesn't.

| Format | How the architect's voice shows |
|---|---|
| `.docx` | Explains the decision to the client's platform team. States the recommendation first, then the mechanism, the trade-off, the rollback and what's still unproven. Owns the call ("we recommend", "this is the right answer for an outage measured in hours"). |
| `.pptx` | Slide titles are the claims the architect would make out loud ("ONLY ONE REGISTRY WRITES AT ANY TIME"). Subtitles are the one sentence they'd add. Speaker notes are what they'd actually say in the room: the point, the evidence, the ask. No slogan copy, no filler slides. |
| `.md` | An internal engineering note from that architect to peers. A little denser and more direct than the .docx. Assumes the reader knows Kafka. Still no hedging and no padding. |

What a senior architect does that a model doesn't:
- **Commits to a recommendation** and names the alternative they rejected and why. They don't lay out a neutral menu.
- **Leads with consequences** for production: what breaks, what's affected, what rolls back, in what order.
- **Separates what's verified from what's inferred**, and says who confirms the inferred part and when.
- **Writes for the operator**, not the reader of a brochure: config keys, modes, owners, exit criteria.
- **Stops when the point is made.**

- **Short, declarative sentences.** Usually 10 to 20 words. One idea per sentence. "Schemas only have to flow one way."
- **Plain words.** "Use" not "leverage". "Set up" not "provision" (unless it's the product's term). "Can't" not "is unable to".
- **Contractions are fine.** "doesn't", "can't", "it's". That's how the reference documents read.
- **"We" for the issuing brand and the joint team.** The issuing brand is GoodLabs Studio by default, or IBM Confluent when the user asks for that (`DESIGN.md` §11). Name no other firm or partner as an author. Name the client's teams by role ("the platform team", "app teams", "whoever owns incidents at <client>").
- **State the decision, then the reason.** "Only CI registers schemas. Producers run with auto-register off." Don't build up to a conclusion.
- **Explain mechanisms in one pass.** "A serialized message carries only the schema ID, not the schema itself." Then say why that matters. Stop there.
- **Be exact about what is known, and frame the gap as a recommendation.** Anything inferred or untested goes in a callout addressed to the team that closes it: "Recommendation for the platform team:", "Recommendation for app teams:" (or both). The callout states what we recommend, then "To test:" with the concrete check that proves it (command, environment, pass condition) and when it must pass. Don't write "To confirm:" or "To prove in the sandbox:" callouts. Never present an inference as a fact, and never stack hedges ("may potentially").
- **Numbers and names, not adjectives.** "In normal running that takes seconds." "About a week once access is in place." Name the config key, the mode, the phase.
- **Rollback and impact are always stated** for any change to production.
- **Pick one spelling convention per document and keep it** (the reference uses "Behaviour"; match the client's convention if they have one).

## 2. De-Claudify: banned patterns

Check every draft against this list before delivering. Each item is a giveaway of model-written text.

**Words and phrases.** Delete them or rewrite the sentence:
- leverage, utilize, robust, seamless(ly), comprehensive, holistic, cutting-edge, state-of-the-art, best-in-class, world-class, powerful, crucial, vital, pivotal, paramount, key (as an adjective in "key considerations"), streamline, empower, unlock, elevate, enhance, foster, delve, navigate (figurative), landscape, realm, journey, tapestry, synergy, ecosystem (unless literally the Confluent ecosystem), game-changer, at its core, under the hood
- "It's worth noting", "It's important to note", "Notably", "Importantly", "Crucially", "Essentially", "Ultimately", "In essence", "Simply put"
- "Let's dive in", "Let's explore", "In this document we will", "This section covers"
- "In conclusion", "To summarize", "In summary" as section openers (an "In short" lead-in before the summary bullets is fine; the reference uses it once)
- "ensure that" (use "make sure", or rewrite as a rule), "in order to" (use "to"), "a wide range of", "various", "a number of"
- "Not only X but also Y", "It's not just X, it's Y", "X isn't merely Y"
- Sign-offs and offers: "I hope this helps", "Feel free to", "Let me know if"

**Punctuation and typography:**
- **No em dashes (—)** in prose. Use a period, a colon or a comma. En dashes are allowed only in number ranges (`2–5`).
- No emoji, no exclamation marks, no ✅/❌ ticks in tables (write "Yes" / "No" or say the actual consequence).
- No arrows (→) in prose. They're fine in diagrams and in a CLI or flow label like `Exporter A → B`.
- Bold is for (a) the one-line rule at the start of a rule-list item, (b) workaround names in "to avoid" lists, (c) callout lead-ins, (d) metadata labels. Don't bold scattered phrases in body text.
- No headings phrased as questions in documents ("What is Schema Linking?"). Deck titles may be plain questions ("WHY NOT TWO WRITERS").
- No title-case headings in documents. Sentence case only.

**Structure:**
- No reflexive triplets ("fast, reliable, and scalable"). List the number of items there actually are.
- No closing paragraph that restates the section. End on the last real point.
- No bullet lists of one or two words. A bullet is a full sentence or a complete clause.
- Use prose for reasoning and lists for parallel facts or ordered steps. A paragraph shouldn't be chopped into bullets.
- No "Overview" or "Introduction" section that only previews later sections. §1 states the problem and the proposal, then maps where the details are.
- No preamble before the first heading, and no meta-commentary about the document itself beyond the map table.
- No marketing comparison ("Confluent's industry-leading…"). Compare on concrete criteria in a table.

**Self-check before delivering:** read the first sentence of every paragraph. Each one should state a fact, a decision or an action. If one opens with framing ("When it comes to…", "In today's…", "One of the most…"), rewrite it.

## 3. Before and after

> **Before:** It's important to note that leveraging Schema Linking provides a robust, seamless way to ensure schemas are comprehensively synchronized across regions — enabling true active/active resilience.
>
> **After:** Schema Linking copies every subject into Region B's default context and keeps the schema IDs. Apps in Region B read locally, so losing Region A doesn't break lookups there.

> **Before:** ✅ **Pros:** Simple! Works everywhere. ❌ **Cons:** Requires a runbook.
>
> **After:** (criteria table) `Change during an outage | Runbook moves the writer to Region B | Works without a runbook`

> **Before:** In conclusion, this phased approach delivers a comprehensive, low-risk migration path that empowers teams to move forward with confidence.
>
> **After:** Until Phase 3, no application reads anything new, and the cluster links are never touched.

## 4. Markdown mode ("give me a Markdown version")

When Markdown is asked for, produce one `.md` file in the senior architect's voice (§1, `.md` row). All of §1–§3 applies, plus:

- **No branding.** No logo, no cover page, no header or footer text, no "Confidential", no HTML, no front matter (unless the destination needs it, e.g. a `wiki/` article that follows `wiki:references:article-format`).
- **Start with a title (`#`)** and then a short metadata line in plain text: `Author · Version · Date · Status`. No badges.
- **Same section skeleton as the Word document** (`DESIGN.md` §11.1), numbered: `## 1. Purpose and summary`, `### 2.1 What is deployed`.
- **Tables** are GitHub pipe tables with the same column shapes as the Word tables. No emoji, no HTML in cells.
- **Figures:** if PNGs exist, reference them with a relative path and an italic caption line below (`*Figure 2. CI writes to Region A; every app reads locally.*`). If they don't, use a Mermaid block only when it's clearer than a sentence. Otherwise write the flow as a numbered list. No ASCII-art boxes.
- **Callouts** are blockquotes with a bold lead-in: `> **Recommendation for the platform team:** … To test: …`. Don't use GitHub alert syntax (`> [!NOTE]`).
- **Code blocks** always name a language (`properties`, `bash`, `sql`, `hcl`).
- **Line length:** one paragraph per line (no hard wrapping), so diffs stay clean.
- **No trailing sections** like "Conclusion", "Summary" or "Further reading" unless they carry new information. End with Open questions and Next steps.
