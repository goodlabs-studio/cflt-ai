# GoodLabs Studio — Design System

A portable spec for producing on-brand GoodLabs Studio material: slide decks, one-pagers, briefs, playbooks, proposals and reference architectures. Drop this file into a Claude Design project (or any design tool) and follow it as the source of truth.

**Precedence:** for Word and PowerPoint deliverables, §11 wins wherever it disagrees with §1–§7. §11 was measured from a delivered client document and deck. The rest of this file covers HTML, artifacts and design-tool work. Writing voice for every format is in `WRITING.md`.

Brand foundations are distilled from goodlabs.studio. The site skews dark and technical: deep black backgrounds, a cyan→blue glowing accent taken from the cloud mark, white type, and editorial serif pull-quotes that lean academic.

---

## 1. Principles

1. **Dark is canonical.** Black canvas, white type. Use light mode (bone page, ink type) for print-heavy documents and long-form reading.
2. **One accent.** The cyan→blue cloud gradient is the only brand color. Use it as a beacon: headline emphasis, section numbers, rules, links. Never as wallpaper.
3. **Type does the work.** Heavy condensed display headlines, quiet body copy, mono labels. Imagery is rare.
4. **Sharp edges.** Panels and tables are square-cornered with 1px hairlines. Only buttons and tags are pills.
5. **Blunt headlines, precise bodies.** Short declarative headlines; specific, quantified body copy. No hype, no emoji.

---

## 2. Logo

- The mark is a cloud with an embedded circuit node in the cyan→blue gradient, followed by the wordmark **GOODLABS** with **STUDIO** set small and letter-spaced beneath.
- Two variants: **black wordmark** for light backgrounds, **white wordmark** for dark backgrounds. Never recolor the mark itself.
- Placement: **top-left** of every page/slide, in the header band. Typical height 20–26px on documents, ~28px on slides.
- Clearspace: at least the height of the cloud mark on all sides.
- Ship the real logo file (SVG preferred, PNG fallback) with this spec — do not redraw it.

---

## 3. Color

### Primitives

| Token | Hex | Use |
|---|---|---|
| `--gl-black` | `#000000` | Dark canvas |
| `--gl-ink` | `#0A0D12` | Cards on dark; primary text on light |
| `--gl-graphite` | `#14181F` | Elevated surface on dark |
| `--gl-slate-900` | `#1C2230` | Body text on light |
| `--gl-slate-700` | `#2A3142` | Secondary text on light |
| `--gl-slate-500` | `#5B6478` | Captions / meta |
| `--gl-slate-300` | `#9AA3B5` | Secondary text on dark |
| `--gl-slate-200` | `#C7CCD6` | Body text on dark |
| `--gl-slate-100` | `#E6E8EE` | Wells / code backgrounds on light |
| `--gl-bone` | `#F5F6F8` | Light-mode page |
| `--gl-white` | `#FFFFFF` | Primary text on dark; cards on light |

### Brand accent (the cloud mark)

| Token | Hex |
|---|---|
| `--gl-cyan-300` | `#5BE3FF` (highlight tip) |
| `--gl-cyan-400` | `#2BC9F5` |
| `--gl-cyan-500` | `#0EAFEC` (dominant cyan — accent on dark) |
| `--gl-blue-500` | `#1E7CE0` |
| `--gl-blue-600` | `#1762C2` (accent on light — legible on white) |
| `--gl-blue-700` | `#0F3F87` |
| `--gl-blue-900` | `#0A2247` (deep tail) |

**Signature gradient**
```css
--gl-grad-cloud:   linear-gradient(135deg, #5BE3FF 0%, #0EAFEC 38%, #1762C2 78%, #0A2247 100%);
--gl-grad-cloud-h: linear-gradient(90deg,  #5BE3FF 0%, #0EAFEC 38%, #1762C2 78%, #0A2247 100%);
```
On light backgrounds, drop the pale tip so gradient text stays legible: `linear-gradient(90deg, #0EAFEC 0%, #1762C2 55%, #0A2247 100%)`.

### Status (sparingly — tables, risk callouts)
`--gl-success #2BC97A` · `--gl-warning #F2B73C` · `--gl-danger #E64545` · `--gl-info #0EAFEC`

### Semantic tokens

| Token | Dark (canonical) | Light |
|---|---|---|
| `--bg` | `#000000` | `#F5F6F8` (bone) |
| `--bg-elev-1` | `#0A0D12` | `#FFFFFF` |
| `--bg-elev-2` | `#14181F` | `#E6E8EE` |
| `--fg-1` primary | `#FFFFFF` | `#0A0D12` |
| `--fg-2` body | `#C7CCD6` | `#1C2230` |
| `--fg-3` secondary | `#9AA3B5` | `#2A3142` |
| `--fg-4` caption | `#5B6478` | `#5B6478` |
| `--accent` | `#0EAFEC` | `#1762C2` |
| `--border-subtle` | `rgba(255,255,255,0.08)` | `rgba(10,13,18,0.08)` |
| `--border-default` | `rgba(255,255,255,0.16)` | `rgba(10,13,18,0.16)` |
| `--border-strong` | `rgba(255,255,255,0.28)` | `rgba(10,13,18,0.28)` |

Hairline = `1px solid var(--border-default)`.

---

## 4. Typography

| Role | Family | Fallbacks | Notes |
|---|---|---|---|
| Display | **Barlow Condensed** 800/900 | Oswald, Helvetica Neue Condensed, Arial | Uppercase, tight tracking (-0.025em), line-height ~0.92–1.04 |
| Sans / UI / body | **Inter** 400–700 | Helvetica Neue, Arial | Body 14–16px, line-height 1.5–1.65 |
| Serif editorial | **Source Serif 4** 400–600, italic | Georgia, Times New Roman | Decks/subtitles, pull-quotes, long-form body in playbooks |
| Mono | **JetBrains Mono** 400–600 | SF Mono, Menlo, Consolas | Eyebrows, section numbers, labels, code |

Google Fonts import:
```css
@import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@500;600;700;800;900&family=Inter:wght@400;500;600;700&family=Source+Serif+4:ital,opsz,wght@0,8..60,400;0,8..60,500;0,8..60,600;1,8..60,400&family=JetBrains+Mono:wght@400;500;600&display=swap');
```

### Scale
| Token | Size |
|---|---|
| `--fs-display-xl` | clamp(56px, 7.2vw, 116px) — hero |
| `--fs-display-lg` | clamp(44px, 5.6vw, 88px) — section H1 |
| `--fs-display-md` | clamp(34px, 4vw, 56px) — H2 |
| h1 / h2 / h3 / h4 | 44 / 32 / 24 / 20px |
| body-lg / body / body-sm | 18 / 16 / 14px |
| caption / eyebrow | 13 / 12px |

Tracking: display `-0.025em`, snug `-0.01em`, wide `0.04em`, eyebrow `0.18em` (all-caps).
Line-height: tight 1.04, snug 1.18, base 1.5, loose 1.65.

### Patterns
- **Eyebrow:** mono, 10–12px, uppercase, `0.18em` tracking, accent color. Sits above titles ("GoodLabs Studio · Executive Brief").
- **Section number:** mono "№ 01" or "01" in accent, inline before the section heading.
- **Gradient emphasis:** one phrase per headline gets the cloud gradient as text fill.
- **Pull-quote:** serif, larger size, with a 2–3px accent rule on the left.
- **Slides:** text never below 24px at 1920×1080.

### Office / Word documents
Brand fonts are rarely installed. For .docx/.pptx handed to others use **Arial** for everything (headings, body, tables, slide text) and **Consolas** for code and config keys. Don't use Calibri, Montserrat or any other font that isn't on every machine. Montserrat on the reference deck's cover fell back to a serif on a machine without it. Full Office specs are in §11.

---

## 5. Spacing, radii, elevation, motion

- **Spacing (4px base):** 4 · 8 · 12 · 16 · 24 · 32 · 48 · 64 · 96 · 128 (`--sp-1` … `--sp-10`)
- **Radii:** panels/tables `0`; small chips `2–4px`; cards (rare) `8px`; buttons/tags `999px` pill.
- **Shadows:** quiet. Prefer the cyan glow over drop shadows:
  - `--glow-cyan: 0 0 0 1px rgba(91,227,255,0.35), 0 0 32px rgba(14,175,236,0.45)`
  - `--glow-cyan-soft: 0 0 24px rgba(14,175,236,0.30)`
- **Ambient orb (dark pages):** a large radial gradient `rgba(91,227,255,0.16) → transparent` in a top corner, behind content.
- **Motion:** ease-out `cubic-bezier(0.22,1,0.36,1)`; 140 / 240 / 480ms.
- **Layout:** container max 1280px; 12-column grid; gutter `clamp(20px, 4vw, 64px)`.

---

## 6. Components

- **Header band (every page/slide):** logo top-left · centered mono reference label in accent · right-aligned mono meta (date, doc number). 1px hairline below.
- **Footer band:** three columns in mono caps — "GoodLabs Studio" · "Confidential · [context]" · "goodlabs.studio" (accent). Hairline above.
- **Buttons:** pill. Primary = white fill / black text on dark (accent fill / black text alt). Secondary = 1px outline. Tertiary = text + →.
- **Panels / cards:** square, 1px hairline, `--bg-elev-1`. Accent variant: cyan border + faint cyan→blue gradient fill.
- **Stat block:** big display number in cloud gradient + mono uppercase label + small caption.
- **Tables:** square, hairline row dividers. Header row either mono-caps on a strong rule (playbooks) or ink/black fill with white caps (briefs). Right-align numbers, tabular figures.
- **Chips / tags:** pill, mono 10–12px; featured chip uses cyan border + cyan text.
- **Callouts:** left accent rule (2–3px) — accent for notes, amber for warnings, red for blocking/anti-patterns.
- **Architecture diagrams:** flow of square blocks with mono labels ("01 / Capture"), display-caps names, small detail text; in-scope blocks get the cyan accent treatment; arrows in accent.

---

## 7. Formats

| Format | Size | Mode |
|---|---|---|
| Slide deck | 1920×1080, 16:9 | Dark (gradient variant for cover/dividers/close) |
| One-pager / executive brief | Letter (816×1056px) or custom tall | Dark or light |
| Long-form playbook / whitepaper | Letter, 1in margins | Light, serif body, sentence-case headings, minimal gradient |
| Proposal / SOW | Letter | Light paper, ink type, accent rules |
| Word (.docx) client document | Letter, 1in side margins | Light. Follow §11.1 exactly |
| PowerPoint (.pptx) client deck | 13.333×7.5in, 16:9 | Dark. Follow §11.2 exactly |

**Playbook register** (lightly branded): logo + thin header/footer, sentence-case sans headings with mono section numbers, serif body at reading size, ruled tables, no all-caps display, at most one gradient touch.

**Sales register** (one-pagers, decks): uppercase condensed display, gradient emphasis, stat blocks, eyebrows, ambient orb.

---

## 8. Voice

- Headlines: short, declarative, often imperative. "Built for production from day one." "Free the data. Protect the engine."
- Body: technical and quantified. Name the system, the number, the timeline.
- Signature lines: "Designed by domain experts. Validated by researchers. Delivered by engineers." · "One embedded team. One accountable lead."
- No hype words, no exclamation points, no emoji.

---

## 9. Drop-in CSS

```css
:root {
  --bg:#000; --bg-elev-1:#0A0D12; --bg-elev-2:#14181F;
  --fg-1:#FFF; --fg-2:#C7CCD6; --fg-3:#9AA3B5; --fg-4:#5B6478;
  --accent:#0EAFEC; --accent-strong:#1762C2;
  --border-default:rgba(255,255,255,0.16);
  --hairline:1px solid var(--border-default);
  --grad:linear-gradient(90deg,#5BE3FF 0%,#0EAFEC 38%,#1762C2 78%,#0A2247 100%);
  --font-display:"Barlow Condensed",Oswald,Arial,sans-serif;
  --font-sans:Inter,"Helvetica Neue",Arial,sans-serif;
  --font-serif:"Source Serif 4",Georgia,serif;
  --font-mono:"JetBrains Mono",Menlo,Consolas,monospace;
}
/* Light mode */
.light {
  --bg:#F5F6F8; --bg-elev-1:#FFF; --bg-elev-2:#E6E8EE;
  --fg-1:#0A0D12; --fg-2:#1C2230; --fg-3:#2A3142; --fg-4:#5B6478;
  --accent:#1762C2; --border-default:rgba(10,13,18,0.16);
  --grad:linear-gradient(90deg,#0EAFEC 0%,#1762C2 55%,#0A2247 100%);
}
.grad-text { background:var(--grad); -webkit-background-clip:text; background-clip:text; -webkit-text-fill-color:transparent; }
.eyebrow  { font:500 11px/1 var(--font-mono); letter-spacing:.18em; text-transform:uppercase; color:var(--accent); }
.display  { font-family:var(--font-display); font-weight:900; text-transform:uppercase; letter-spacing:-.025em; line-height:.92; }
```

---

## 10. Don'ts

- Don't add a second accent color or recolor the logo.
- Don't use drop shadows heavier than the tokens; prefer the cyan glow.
- Don't round panels or tables.
- Don't fill backgrounds with the gradient; keep it to text, rules, and small fills.
- Don't use decorative illustration or stock AI imagery; use real product/architecture diagrams or nothing.
- Don't set slide text below 24px or document body below ~10.5pt.

---

## 11. Office deliverables (.docx / .pptx)

These specs come from a GoodLabs client document and deck delivered in November 2026: a 10-page solution design and an 11-slide companion deck. Values were measured from the files. Copy them as written. When you're asked for documentation, use the Word spec. When a deck is asked for, use the PowerPoint spec. When both are asked for, make a matched pair (§11.4). Content and voice rules are in `WRITING.md`.

**Issuing brand.** Every deliverable comes from exactly one issuing brand, and that brand is the only one represented. No client logo, no client branding and no other partner names appear anywhere, and no client is named as a template or reference source.

| Issuing brand | When | Mark in header / deck cover | Wordmark | Byline name |
|---|---|---|---|---|
| **GoodLabs Studio** (default) | Unless the user says otherwise | `assets/brand/mark.png` | `assets/brand/logo-black.png` | GoodLabs Studio |
| **IBM Confluent** | Only when the user asks for the deliverable to come from IBM Confluent | IBM Confluent logo file supplied by the user | Same file | IBM Confluent |

GoodLabs logo files: `assets/brand/mark.png` (cloud mark only), `assets/brand/logo-black.png` (mark + wordmark, for light pages), `assets/brand/logo.svg`. Use them as they are. There's no IBM Confluent logo in the repo. Ask the user for the file, and until it arrives use the brand name as text in the logo's place. Never redraw, recolor or recreate any logo. Below, `<Brand>` means the issuing brand's name.

### 11.1 Word document (light)

**Implementation.** `tools/md2docx/` applies this spec: `build_reference.py` holds the styles, and `md2docx.py` adds the header, footer and page setup. When you change a value in this section, change it there too and re-run `build_reference.py`, or new documents won't follow it.

**Page.** US Letter, portrait. Margins: left and right 1in, top and bottom 0.9in. Header and footer distance 0.49in. Usable width 6.5in.

**Fonts.** Arial for all text. Consolas for code blocks and inline config keys, mode names and CLI flags. Nothing else.

| Element | Spec |
|---|---|
| Body | Arial 10.5pt, `#222222`, line spacing 1.25, 6pt after, left-aligned (never justified) |
| H1 | `N. Title`. Arial Bold 17pt, `#0F172A`, 18pt before, 6pt after, sentence case |
| H2 | `N.M Title`. Arial Bold 12.5pt, `#0F8FC2`, 10pt before, 4pt after, sentence case |
| H3 (run-in) | Unnumbered label above a step list ("During the outage"). Arial Bold 10.5pt, `#0F172A` |
| Bullets | `•`, indent 0.375in, hanging 0.19in, 4pt after, line spacing 1.2 |
| Numbered steps | `1.` decimal, same indents. Use them only when order matters |
| Rule lists | Numbered. Each item starts with a bold one-line rule and a period, then a plain explanation |
| Inline code | Consolas 9.5pt, same color as body, no shading |
| Code block | Consolas 9pt, paragraph fill `#F1F4F7`, 0.08in left indent, 0pt between lines, no border. One block per config set |
| Callout | Paragraph fill `#EAF4FA`, left border 4.5pt `#0F8FC2`, bold lead-in ending in a colon naming the audience ("Recommendation for the platform team:", "Recommendation for app teams:"), body 10.5pt with the recommendation, then "To test:" and the check |
| Figure | PNG, centered, at most 6.5in wide, 6pt before. Caption below, centered, Arial Italic 9pt `#5B6478`: `Figure N. <sentence stating what the figure shows>` |

**Tables.** Full width (6.5in). Header row filled `#0F172A`, Arial Bold 10pt white, sentence-case labels. Body cells Arial 10pt `#222222`, cell padding about 0.08in. Bold the first column when it labels the row. Borders are 0.5pt light grey-blue on every edge. No zebra striping, no merged cells. Number tables only when the text refers to them. Common shapes:
- Map: `Topic | Type | Covered in` (§1 only)
- Current state: `Component | Current state`
- Comparison: `Component | Option A | Option B`, or `Criterion | <proposed> (proposed) | <alternative>`
- Phases: `Phase | Goal | Production impact | Rollback`
- Plan-for items: `Topic | Detail`
- Open questions: `Question | Owner | Why it matters`

**Header (every page).** The issuing brand's mark at top left, about 0.45in tall. Right-aligned in the same band: `<Brand> · <document type>` (for example `GoodLabs Studio · Solution Design` or `IBM Confluent · Migration Runbook`), Arial 9pt `#5B6478`, with ` · ` separators. No rule line.

**Footer (every page).** Right-aligned: `<document title, short> · Page N`, Arial 9pt `#5B6478`, with N as a PAGE field. No client name and no "Confidential" marking.

**No title page.** The document gets straight into it. Page 1 opens with:
1. The document title: Arial Bold 20pt `#0F172A`, sentence case, 0pt before, 4pt after.
2. One metadata line: `<Author>, <Brand> · Version X.Y · <Month YYYY> · <status>`, Arial 9.5pt `#5B6478`, 14pt after. Add `· Companion: <title>` when there is a companion document.
3. Section 1 straight after.

No client name, client logo or `<Client>` placeholder anywhere in the document. Refer to the client's teams by role ("the platform team", "app teams").

**Body skeleton.** Use this for a design or solution document. Drop sections that don't apply; don't add filler to keep one.
1. **Purpose and summary.** Situation in two or three sentences. The problem. "In short" followed by three to five bullets stating the proposal. One paragraph on the key insight. A `Topic | Type | Covered in` map table.
2. **Current setup and the problem.** Figure 1 (current state). 2.1 What is deployed (table). 2.2 Why it fails. A recommendation callout, addressed to the team that closes it, for anything inferred and not verified. 2.3 Workarounds to avoid: bullets, each a bold sentence naming the workaround and then why it fails.
3. **Target design.** One paragraph on what changes and what doesn't. Figure 2. Comparison table. 3.1 Rules (numbered rule list). 3.2 Why it works. 3.3 Client configuration (code block).
4. **Process sections.** One per workflow (change process, operations). Each has a figure and its prose.
5. **Failure modes.** One H2 per scenario. Steps go under H3 run-in labels ("During the outage", "When Region A is back"). End with a recommendation callout that says how each untested item is tested and by which team.
6. **Alternative considered.** What it was, a criteria table, and a closing paragraph on when to revisit it.
7. **Implementation path.** One paragraph on why the phases run in this order. A phase figure and a phase table. One H2 per phase with bullets, ending "Done when <exit criterion>."
8. **Points to plan for** (`Topic | Detail`).
9. **Open questions** (`Question | Owner | Why it matters`).
10. **Next steps.** Numbered. Each step is something a named person or team will do.

### 11.2 PowerPoint deck (dark)

**Canvas.** 13.333×7.5in (16:9). Background solid `#000000` on every slide, set in the master. Arial on every run.

**Palette (deck only).**

| Role | Hex |
|---|---|
| Background | `#000000` |
| Card / callout fill | `#1A1A1A`, rounded rectangle, no outline |
| Title / card heading | `#FFFFFF` |
| Body text | `#E3E3E3` |
| Subtitle, footer, labels | `#9A9A9A` |
| Primary accent: eyebrows, chips, key lines, table header text, step numbers | `#1FC4F4` |
| Secondary accent: owners, actions, warnings, "why it matters" | `#F7B731` |
| Table borders | `#373736` / `#474646`, 1pt |

Amber is the only second accent. Use it for who/what-next and for caveats, never decoration.

**Content slide layout** (every slide after the cover, positions in inches from top left):

| Element | Position / size | Type |
|---|---|---|
| Eyebrow `NN · SECTION` | x 0.5, y 0.31, w 12.7 | Arial Bold 12pt `#1FC4F4`, all caps, `·` separator |
| Title | x 0.5, y 0.63, w 12.7 | Arial Bold 30pt white, all caps, one line |
| Subtitle | x 0.5, y 1.17, w 12.7 | Arial 14pt `#9A9A9A`, one sentence, sentence case |
| Content area | y 1.7 to 6.9, x 0.5 to 12.83 | — |
| Footer left | x 0.5, y 7.06 | Arial 10pt `#9A9A9A`, caps: `<BRAND> · <CLIENT PROGRAM> · <DECK TITLE>` |
| Page number | x 12.22, y 7.06, right-aligned | Arial 10pt `#9A9A9A` |

The eyebrow number matches the section number in the companion document (`03 · TARGET` ↔ doc §3).

**Content patterns.** Use these and nothing else:
- **Diagram slide:** one full-width PNG in the content area, with an optional one-line callout bar under it.
- **Card grid:** 2×2 cards (6.09×1.6in each) or 1×3 cards (3.99×2.6in), 0.15in gaps. Each card has a numbered circle (0.39in, fill `#1FC4F4` for rules or `#F7B731` for actions, black bold 13pt number), a heading in Arial Bold 15pt white, and body in Arial 12pt `#E3E3E3`, at most three lines. Action cards add an `OWNER` label (Arial Bold 10pt `#9A9A9A`) above the owner's name in Arial Bold 12pt `#F7B731`.
- **Table slide:** the table at y 1.7, full width, Arial 12pt. Header text bold `#1FC4F4`, no fill. First column bold. Body `#E3E3E3`. Cell margins 0.15in × 0.1in.
- **Callout bar:** a `#1A1A1A` rounded rectangle, full content width, about 0.5in tall. One sentence in Arial Bold 13pt, cyan for the takeaway or amber for a caveat. At most one per slide.

**Cover slide.** Black. The issuing brand's mark at top left (x 0.75, y 0.72, about 1.2in wide). Nothing at top right: no client logo. Title at x 0.75, y 2.04: Arial Bold 48pt white, all caps, two lines, ending with a period ("SCHEMA REGISTRY / FOR ACTIVE/ACTIVE."). Subtitle at y 4.34: Arial 19pt `#E3E3E3`, one sentence stating the design. A row of four chips at y 5.05 (2.74×0.36in each): cyan 1pt outline, no fill, Arial Bold 12pt `#1FC4F4` caps, each a two-to-four-word claim. Purpose line at y 5.75: Arial Bold 15pt `#1FC4F4`, saying who the deck is for and when ("For review with the <client> platform team before Phase 0 starts."). Byline at y 6.6: Arial 12pt `#9A9A9A`, `Prepared for <Client> by <Brand> · <Month YYYY>`.

**Deck skeleton** (it follows the document, one idea per slide): 1 cover · 2 `01 · SUMMARY` proposal table (`Area | Proposal`) and takeaway bar · 3 `02 · TODAY` current-state diagram · 4 `03 · TARGET` target diagram · 5 `03 · TARGET` rules card grid with "why it matters" amber card · 6 process diagram and two audience cards ("For developers" / "For the pipeline") · 7 failure-mode diagram and caveat bar · 8 alternative comparison table · 9 phase diagram and safety bar · 10 open questions table (`Question | Who | Why it matters`) · 11 `NN · NEXT STEPS` 1×3 action cards with owners and a closing bar pointing to the companion document.

**Titles** are claims or plain questions in caps: "ONE WRITER, BOTH REGIONS READ", "ONLY ONE REGISTRY WRITES AT ANY TIME", "WHY NOT TWO WRITERS", "WHAT WE NEED FROM <CLIENT>". Don't use topic labels like "ARCHITECTURE" or "OVERVIEW".

**Speaker notes on every slide.** One to three sentences of what the presenter says: the point, the evidence, and the ask. Use the same plain voice as the document.

**Text floor.** Nothing under 10pt (footer), body at least 12pt. This replaces the 24px HTML-slide floor in §4 for .pptx.

### 11.3 Diagrams (PNG, both formats)

Render diagrams as PNG and insert them as images. Don't build them from Office shapes.

| | Document | Deck |
|---|---|---|
| Canvas | White or `#F3F7FA` background, 1920px wide (2× for 6.5in) | `#000000` background, 3200px wide |
| Containers | Regions/zones are a rounded 1px `#C9D3DE` outline with a caps label and a gray descriptor ("REGION A  schema writer") | Same, `#2A2A2A` outline, `#111111` fill |
| Boxes | Rounded 6px, 1px border. Bold title line, then one gray detail line, plus mono lines for config | `#1A1A1A` fill, same structure |
| State colors | Blue `#0F8FC2` = writer / active · green = copy / import · amber = CI, human action, approval · red = failure / denied · dashed gray = unavailable | Same hues, brightened (cyan `#1FC4F4`, green `#3DDC84`, amber `#F7B731`, red `#E64545`), boxes tinted with about 15% of the hue |
| Badges | Small caps pill after a box title: `READWRITE`, `IMPORT`, `EMPTY`, `UNREACHABLE` | Same |
| Arrows | 1.5px, label sits on a background-colored patch next to the line. Dashed means a check or a stopped/paused flow | Same |
| Font | Inter (fallback Arial), mono for config | Same |

A diagram shows one state or one flow. For a before/during/after story, use columns in one figure ("Normal running · Region A down · …"), each with a one-line caption under it. Every figure in the document gets a numbered caption. In the deck, the slide title does that job.

### 11.4 Matched document + deck

- Same section numbering. Deck eyebrows reuse the document's section numbers.
- Same diagrams: the deck uses the dark render, the document the light render.
- Same terms, same table rows (the deck may shorten cell text, but never changes meaning).
- The document's metadata line names the deck as its companion. The deck's last slide points to the document.
- Ship both with the same version number and date.
