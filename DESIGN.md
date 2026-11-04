# GoodLabs Studio — Design System

A portable spec for producing on-brand GoodLabs Studio material: slide decks, one-pagers, briefs, playbooks, proposals and reference architectures. Drop this file into a Claude Design project (or any design tool) and follow it as the source of truth.

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
Brand fonts are rarely installed. For .docx/.pptx handed to others, substitute **Arial** (sans/headings), **Georgia** (serif body), **Consolas** (mono) so layout holds on any machine.

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
| Word / PowerPoint export | Letter / 16:9 | Light; system-font substitutions (§4) |

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
