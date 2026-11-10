#!/usr/bin/env python3
"""Build reference.docx for pandoc from pandoc's default, restyled to DESIGN.md §11.1.

Run once (or after a DESIGN.md §11.1 change):
    python3 tools/md2docx/build_reference.py
Writes tools/md2docx/reference.docx. Header, footer and page setup are added per
document by md2docx.py, because they carry the document's own title and type.
"""
import re
import subprocess
import sys
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "reference.docx"

INK, BLUE, BODY, MUTED, BORDER = "0F172A", "0F8FC2", "222222", "5B6478", "C9D3DE"
CALLOUT_FILL, CODE_FILL = "EAF4FA", "F1F4F7"
ARIAL = '<w:rFonts w:ascii="Arial" w:hAnsi="Arial" w:eastAsia="Arial" w:cs="Arial"/>'
MONO = '<w:rFonts w:ascii="Consolas" w:hAnsi="Consolas" w:eastAsia="Consolas" w:cs="Consolas"/>'


def sz(half_points):
    return f'<w:sz w:val="{half_points}"/><w:szCs w:val="{half_points}"/>'


def pstyle(sid, name, ppr="", rpr="", based="Normal", nxt=None, custom=False):
    c = ' w:customStyle="1"' if custom else ""
    n = f'<w:next w:val="{nxt}"/>' if nxt else ""
    return (f'<w:style w:type="paragraph"{c} w:styleId="{sid}"><w:name w:val="{name}"/>'
            f'<w:basedOn w:val="{based}"/>{n}<w:qFormat/><w:pPr>{ppr}</w:pPr><w:rPr>{rpr}</w:rPr></w:style>')


STYLES = [
    # Font, size and color live in docDefaults, not Normal: a paragraph style's color would
    # override the table style's white header text.
    pstyle("Normal", "Normal", "", "", based=None),
    pstyle("BodyText", "Body Text", '<w:spacing w:before="0" w:after="120" w:line="300" w:lineRule="auto"/>'),
    pstyle("FirstParagraph", "First Paragraph", "", "", based="BodyText", nxt="BodyText", custom=True),
    # Tight list items and table cells pandoc doesn't wrap.
    pstyle("Compact", "Compact", '<w:spacing w:before="0" w:after="80" w:line="288" w:lineRule="auto"/>', based="BodyText", custom=True),
    pstyle("Title", "Title", '<w:spacing w:before="0" w:after="80"/>', f'<w:b/><w:color w:val="{INK}"/>{sz(40)}', nxt="BodyText"),
    pstyle("Subtitle", "Subtitle", '<w:spacing w:after="280"/>', f'<w:color w:val="{MUTED}"/>{sz(19)}', nxt="BodyText"),
    pstyle("Metadata", "Metadata", '<w:spacing w:before="0" w:after="280"/>', f'<w:color w:val="{MUTED}"/>{sz(19)}', based="BodyText", custom=True),
    pstyle("Heading1", "heading 1", '<w:keepNext/><w:keepLines/><w:spacing w:before="360" w:after="120"/><w:outlineLvl w:val="0"/>',
           f'<w:b/><w:color w:val="{INK}"/>{sz(34)}', nxt="BodyText"),
    pstyle("Heading2", "heading 2", '<w:keepNext/><w:keepLines/><w:spacing w:before="200" w:after="80"/><w:outlineLvl w:val="1"/>',
           f'<w:b/><w:color w:val="{BLUE}"/>{sz(25)}', nxt="BodyText"),
    pstyle("Heading3", "heading 3", '<w:keepNext/><w:keepLines/><w:spacing w:before="120" w:after="60"/><w:outlineLvl w:val="2"/>',
           f'<w:b/><w:color w:val="{INK}"/>{sz(21)}', nxt="BodyText"),
    # Run-in label: a paragraph that is only bold text ("**Rollback**").
    pstyle("Label", "Label", '<w:keepNext/><w:spacing w:before="120" w:after="60"/>', f'<w:b/><w:color w:val="{INK}"/>',
           based="BodyText", custom=True),
    # Callout: blockquote in Markdown.
    pstyle("BlockText", "Block Text",
           f'<w:pBdr><w:left w:val="single" w:sz="36" w:space="8" w:color="{BLUE}"/></w:pBdr>'
           f'<w:shd w:val="clear" w:color="auto" w:fill="{CALLOUT_FILL}"/>'
           '<w:spacing w:before="120" w:after="160" w:line="288" w:lineRule="auto"/><w:ind w:left="160" w:right="80"/>',
           "", based="BodyText", nxt="BodyText"),
    pstyle("SourceCode", "Source Code",
           f'<w:shd w:val="clear" w:color="auto" w:fill="{CODE_FILL}"/><w:wordWrap w:val="off"/>'
           '<w:spacing w:before="60" w:after="140" w:line="240" w:lineRule="auto"/><w:ind w:left="115"/>',
           f'{MONO}{sz(18)}', custom=True),
    pstyle("TableText", "Table Text", '<w:spacing w:before="0" w:after="0" w:line="264" w:lineRule="auto"/>', sz(20), custom=True),
    pstyle("TableHeader", "Table Header", '<w:keepNext/><w:spacing w:before="0" w:after="0" w:line="264" w:lineRule="auto"/>',
           f'<w:b/><w:color w:val="FFFFFF"/>{sz(20)}', custom=True),
    pstyle("Figure", "Figure", '<w:keepNext/><w:jc w:val="center"/><w:spacing w:before="120" w:after="60"/>', "", custom=True),
    pstyle("CaptionedFigure", "Captioned Figure", '<w:keepNext/><w:jc w:val="center"/><w:spacing w:before="120" w:after="60"/>', "",
           based="Figure", custom=True),
    pstyle("Caption", "caption", '<w:jc w:val="center"/><w:spacing w:before="0" w:after="200"/>', f'<w:i/><w:color w:val="{MUTED}"/>{sz(18)}'),
    pstyle("ImageCaption", "Image Caption", "", "", based="Caption", custom=True),
    pstyle("TableCaption", "Table Caption", "", "", based="Caption", custom=True),
    '<w:style w:type="character" w:customStyle="1" w:styleId="VerbatimChar"><w:name w:val="Verbatim Char"/>'
    f'<w:rPr>{MONO}{sz(19)}</w:rPr></w:style>',
    '<w:style w:type="table" w:default="1" w:styleId="Table"><w:name w:val="Table"/><w:basedOn w:val="TableNormal"/><w:qFormat/>'
    '<w:tblPr><w:tblInd w:w="0" w:type="dxa"/><w:tblBorders>'
    + "".join(f'<w:{e} w:val="single" w:sz="4" w:space="0" w:color="{BORDER}"/>' for e in ("top", "left", "bottom", "right", "insideH", "insideV"))
    + '</w:tblBorders><w:tblCellMar><w:top w:w="80" w:type="dxa"/><w:left w:w="115" w:type="dxa"/>'
    '<w:bottom w:w="80" w:type="dxa"/><w:right w:w="115" w:type="dxa"/></w:tblCellMar></w:tblPr>'
    '<w:trPr><w:cantSplit/></w:trPr><w:tcPr><w:vAlign w:val="top"/></w:tcPr>'
    f'<w:tblStylePr w:type="firstRow"><w:rPr><w:b/><w:color w:val="FFFFFF"/></w:rPr><w:trPr><w:tblHeader/></w:trPr>'
    f'<w:tcPr><w:shd w:val="clear" w:color="auto" w:fill="{INK}"/></w:tcPr></w:tblStylePr></w:style>',
]


def main():
    default = HERE / "_default-reference.docx"
    subprocess.run(["pandoc", "-o", str(default), "--print-default-data-file", "reference.docx"], check=True)
    with zipfile.ZipFile(default) as zin:
        files = {n: zin.read(n) for n in zin.namelist() if not n.endswith("/")}
    styles = files["word/styles.xml"].decode()

    # Drop pandoc's versions of every style we define, plus their linked character styles.
    ids = [re.search(r'w:styleId="([^"]+)"', s).group(1) for s in STYLES]
    for sid in ids + [f"{i}Char" for i in ids]:
        styles = re.sub(rf'<w:style [^>]*w:styleId="{sid}".*?</w:style>', "", styles, flags=re.S)
    styles = re.sub(r"<w:link w:val=\"[^\"]+\"\s*/>", "", styles)
    # Arial 10.5pt body text by default.
    styles = re.sub(r"<w:docDefaults>.*?</w:docDefaults>",
                    f'<w:docDefaults><w:rPrDefault><w:rPr>{ARIAL}<w:color w:val="{BODY}"/>{sz(21)}<w:lang w:val="en-US"/></w:rPr></w:rPrDefault>'
                    '<w:pPrDefault><w:pPr><w:spacing w:after="120"/></w:pPr></w:pPrDefault></w:docDefaults>',
                    styles, flags=re.S)
    styles = styles.replace("</w:styles>", "".join(STYLES) + "</w:styles>")
    # Normal has no basedOn.
    styles = styles.replace('<w:basedOn w:val="None"/>', "")
    files["word/styles.xml"] = styles.encode()

    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as zout:
        for n, data in files.items():
            zout.writestr(n, data)
    default.unlink()
    print("wrote", OUT)


if __name__ == "__main__":
    sys.exit(main())
