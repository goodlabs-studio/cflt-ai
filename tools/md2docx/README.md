# md2docx

Converts a Markdown document written to `WRITING.md` §4 into a Word document laid out to `DESIGN.md` §11.1. It uses pandoc and no model tokens, so the Markdown first pass becomes a Word document in about a second.

```bash
brew install pandoc        # once
python3 tools/md2docx/md2docx.py path/to/doc.md                      # writes path/to/doc.docx
python3 tools/md2docx/md2docx.py doc.md --doc-type "DR Runbook"      # header label
python3 tools/md2docx/md2docx.py doc.md --brand ibm                  # IBM Confluent header (text only, no logo yet)
python3 tools/md2docx/md2docx.py doc.md --short-title "DR runbook"   # footer text
```

The header label comes from the title by default ("runbook" gives "Runbook"). The footer text is the title up to its first colon.

## What the Markdown needs

| Markdown | Word |
|---|---|
| `# Title` on the first line | Title, 20pt bold |
| The paragraph after it | Metadata line |
| `## 1. Section`, `### 1.1 Subsection` | Heading 1, Heading 2 |
| A paragraph that is only `**Label**` | Run-in label |
| Pipe table, first column in `**bold**` | Ink header row, bordered cells; column widths come from the content |
| `> **Recommendation for the platform team:** … To test: …` | Callout with the blue left bar |
| Fenced code block with a language | Shaded Consolas block |
| `![Figure 1](figs/fig1.png)` then `*Figure 1. Caption.*` on the next line | Figure at full text width with that caption |

## Files

- `md2docx.py` runs pandoc, then adds the brand header, the `<short title> · Page N` footer and US Letter page setup.
- `md2docx.lua` is the pandoc filter: it handles the title and metadata line, shifts headings, and sets labels, figures and table widths.
- `build_reference.py` builds `reference.docx` (the styles) from pandoc's default. It is committed with the tool and rebuilt automatically if missing. Re-run it after a `DESIGN.md` §11.1 change.

There is no PDF step: export from Word.
