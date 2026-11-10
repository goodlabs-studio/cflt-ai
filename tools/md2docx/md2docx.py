#!/usr/bin/env python3
"""Convert a WRITING.md §4 Markdown document to a DESIGN.md §11.1 Word document.

    python3 tools/md2docx/md2docx.py runbook.md
    python3 tools/md2docx/md2docx.py runbook.md -o out.docx --doc-type "DR Runbook" --brand ibm

pandoc does the conversion with reference.docx (styles) and md2docx.lua (structure).
This script then adds what changes per document: the brand header, the footer
"<short title> · Page N", and US Letter page setup. No model tokens are involved.
"""
import argparse
import re
import subprocess
import sys
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
MARK = REPO / "assets" / "brand" / "mark.png"
BRANDS = {"goodlabs": "GoodLabs Studio", "ibm": "IBM Confluent"}
MUTED = "5B6478"

NS = ('xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" '
      'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
      'xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" '
      'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
      'xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture"')
RUN = f'<w:rPr><w:rFonts w:ascii="Arial" w:hAnsi="Arial" w:cs="Arial"/><w:color w:val="{MUTED}"/><w:sz w:val="18"/><w:szCs w:val="18"/></w:rPr>'
REL_IMG = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/image"
REL_HDR = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/header"
REL_FTR = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/footer"


def logo_run():
    # mark.png is 497 x 299 px; 0.45in tall in the header.
    cy = int(0.45 * 914400)
    cx = int(cy * 497 / 299)
    return (f'<w:r><w:drawing><wp:inline distT="0" distB="0" distL="0" distR="0"><wp:extent cx="{cx}" cy="{cy}"/>'
            '<wp:docPr id="9001" name="mark" descr="GoodLabs mark"/><wp:cNvGraphicFramePr><a:graphicFrameLocks noChangeAspect="1"/>'
            '</wp:cNvGraphicFramePr><a:graphic><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">'
            '<pic:pic><pic:nvPicPr><pic:cNvPr id="0" name="mark.png"/><pic:cNvPicPr/></pic:nvPicPr><pic:blipFill>'
            '<a:blip r:embed="rIdMark"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill><pic:spPr><a:xfrm><a:off x="0" y="0"/>'
            f'<a:ext cx="{cx}" cy="{cy}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr></pic:pic>'
            '</a:graphicData></a:graphic></wp:inline></w:drawing></w:r>')


def header_xml(brand, doc_type):
    logo = logo_run() if brand == "goodlabs" else ""
    text = f"\t{BRANDS[brand]} · {doc_type}"
    return (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:hdr {NS}><w:p><w:pPr>'
            '<w:tabs><w:tab w:val="right" w:pos="9360"/></w:tabs></w:pPr>'
            f'{logo}<w:r>{RUN}<w:t xml:space="preserve">{escape(text)}</w:t></w:r></w:p></w:hdr>')


def footer_xml(short_title):
    return (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:ftr {NS}><w:p><w:pPr><w:jc w:val="right"/></w:pPr>'
            f'<w:r>{RUN}<w:t xml:space="preserve">{escape(short_title)} · Page </w:t></w:r>'
            f'<w:r>{RUN}<w:fldChar w:fldCharType="begin"/></w:r><w:r>{RUN}<w:instrText xml:space="preserve"> PAGE </w:instrText></w:r>'
            f'<w:r>{RUN}<w:fldChar w:fldCharType="separate"/></w:r><w:r>{RUN}<w:t>1</w:t></w:r>'
            f'<w:r>{RUN}<w:fldChar w:fldCharType="end"/></w:r></w:p></w:ftr>')


SECT = ('<w:sectPr><w:headerReference w:type="default" r:id="rIdMdHdr"/><w:footerReference w:type="default" r:id="rIdMdFtr"/>'
        '<w:pgSz w:w="12240" w:h="15840"/><w:pgMar w:top="1296" w:right="1440" w:bottom="1296" w:left="1440" '
        'w:header="706" w:footer="706" w:gutter="0"/></w:sectPr>')


def title_of(md_text):
    m = re.search(r"^# (.+)$", md_text, re.M)
    return m.group(1).strip() if m else "Document"


def default_doc_type(title):
    t = title.lower()
    for word, label in (("runbook", "Runbook"), ("design", "Solution Design"), ("guide", "Guide"), ("proposal", "Proposal")):
        if word in t:
            return label
    return "Document"


def style_table(m):
    """Header row paragraphs get Table Header, the rest Table Text (pandoc uses Compact)."""
    tbl = m.group(0)
    rows = re.split(r"(?=<w:tr[ >])", tbl)
    out = []
    for row in rows:
        style = "TableHeader" if "<w:tblHeader" in row else "TableText"
        out.append(row.replace('<w:pStyle w:val="Compact" />', f'<w:pStyle w:val="{style}" />')
                      .replace('<w:pStyle w:val="Compact"/>', f'<w:pStyle w:val="{style}"/>'))
    return "".join(out)


def postprocess(docx, brand, doc_type, short_title):
    with zipfile.ZipFile(docx) as zin:
        files = {n: zin.read(n) for n in zin.namelist() if not n.endswith("/")}

    doc = files["word/document.xml"].decode()
    doc = re.sub(r"<w:tbl>.*?</w:tbl>", style_table, doc, flags=re.S)
    doc = re.sub(r"<w:sectPr\b.*?</w:sectPr>(?=\s*</w:body>)", "", doc, flags=re.S)
    doc = doc.replace("</w:body>", SECT + "</w:body>")
    files["word/document.xml"] = doc.encode()

    files["word/header-md2docx.xml"] = header_xml(brand, doc_type).encode()
    files["word/footer-md2docx.xml"] = footer_xml(short_title).encode()
    if brand == "goodlabs":
        files["word/media/md2docx-mark.png"] = MARK.read_bytes()
        files["word/_rels/header-md2docx.xml.rels"] = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            f'<Relationship Id="rIdMark" Type="{REL_IMG}" Target="media/md2docx-mark.png"/></Relationships>').encode()

    rels = files["word/_rels/document.xml.rels"].decode()
    rels = rels.replace("</Relationships>",
                        f'<Relationship Id="rIdMdHdr" Type="{REL_HDR}" Target="header-md2docx.xml"/>'
                        f'<Relationship Id="rIdMdFtr" Type="{REL_FTR}" Target="footer-md2docx.xml"/></Relationships>')
    files["word/_rels/document.xml.rels"] = rels.encode()

    ct = files["[Content_Types].xml"].decode()
    add = ('<Override PartName="/word/header-md2docx.xml" '
           'ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.header+xml"/>'
           '<Override PartName="/word/footer-md2docx.xml" '
           'ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.footer+xml"/>')
    if 'Extension="png"' not in ct:
        add += '<Default Extension="png" ContentType="image/png"/>'
    files["[Content_Types].xml"] = ct.replace("</Types>", add + "</Types>").encode()

    # Rewrite without directory entries (Word on co-editing services rejects them).
    tmp = docx.with_suffix(".tmp")
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
        order = ["[Content_Types].xml"] + [n for n in files if n != "[Content_Types].xml"]
        for n in order:
            zout.writestr(n, files[n])
    tmp.replace(docx)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("markdown", type=Path)
    ap.add_argument("-o", "--output", type=Path, help="default: same name, .docx")
    ap.add_argument("--brand", choices=sorted(BRANDS), default="goodlabs")
    ap.add_argument("--doc-type", help='header label, e.g. "DR Runbook" (default: from the title)')
    ap.add_argument("--short-title", help="footer text (default: the title up to its first colon)")
    args = ap.parse_args()

    ref = HERE / "reference.docx"
    if not ref.exists():  # rebuilt from build_reference.py if missing
        subprocess.run([sys.executable, str(HERE / "build_reference.py")], check=True)

    md = args.markdown.resolve()
    out = (args.output or md.with_suffix(".docx")).resolve()
    title = title_of(md.read_text())
    short_title = args.short_title or title.split(":")[0].strip()
    doc_type = args.doc_type or default_doc_type(title)

    subprocess.run([
        "pandoc", str(md), "-f", "markdown-raw_html-smart-tex_math_dollars", "-t", "docx", "-o", str(out),
        "--reference-doc", str(HERE / "reference.docx"),
        "--lua-filter", str(HERE / "md2docx.lua"),
        "--resource-path", str(md.parent),
        "--syntax-highlighting=none",
    ], check=True)
    postprocess(out, args.brand, doc_type, short_title)
    print("wrote", out)


if __name__ == "__main__":
    sys.exit(main())
