#!/usr/bin/env python3
"""Build the Sleep Tight literature review PDF with ReportLab."""

from __future__ import annotations

import csv
import html
import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    HRFlowable,
    KeepTogether,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.platypus.tableofcontents import TableOfContents


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "research" / "09-deep-literature-review.md"
MATRIX = ROOT / "research" / "evidence-matrix.csv"
OUTPUT = ROOT / "output" / "pdf" / "sleep-tight-critical-literature-review.pdf"

NAVY = colors.HexColor("#14243A")
INK = colors.HexColor("#263442")
AMBER = colors.HexColor("#D98C2B")
PALE_AMBER = colors.HexColor("#FFF5E7")
PALE_BLUE = colors.HexColor("#EEF4F8")
MID_BLUE = colors.HexColor("#53738A")
LIGHT_LINE = colors.HexColor("#D7E0E6")
MUTED = colors.HexColor("#607381")
WHITE = colors.white


def register_fonts() -> None:
    base = Path("/System/Library/Fonts/Supplemental")
    pdfmetrics.registerFont(TTFont("ST-Regular", str(base / "Arial.ttf")))
    pdfmetrics.registerFont(TTFont("ST-Bold", str(base / "Arial Bold.ttf")))
    pdfmetrics.registerFont(TTFont("ST-Italic", str(base / "Arial Italic.ttf")))
    pdfmetrics.registerFont(TTFont("ST-BoldItalic", str(base / "Arial Bold Italic.ttf")))
    pdfmetrics.registerFontFamily(
        "ST",
        normal="ST-Regular",
        bold="ST-Bold",
        italic="ST-Italic",
        boldItalic="ST-BoldItalic",
    )


class ReviewDocTemplate(BaseDocTemplate):
    def __init__(self, filename: str, **kwargs):
        super().__init__(filename, **kwargs)
        frame = Frame(
            self.leftMargin,
            self.bottomMargin,
            self.width,
            self.height,
            id="content",
            leftPadding=0,
            rightPadding=0,
            topPadding=0,
            bottomPadding=0,
        )
        self.addPageTemplates(PageTemplate(id="main", frames=[frame], onPage=self.draw_page))

    def draw_page(self, canvas, doc):
        page = canvas.getPageNumber()
        width, height = A4
        canvas.saveState()
        if page == 1:
            canvas.setFillColor(NAVY)
            canvas.rect(0, 0, width, height, stroke=0, fill=1)
            canvas.setFillColor(AMBER)
            canvas.rect(0, 0, 16 * mm, height, stroke=0, fill=1)
            canvas.restoreState()
            return

        canvas.setStrokeColor(LIGHT_LINE)
        canvas.setLineWidth(0.5)
        canvas.line(doc.leftMargin, height - 17 * mm, width - doc.rightMargin, height - 17 * mm)
        canvas.setFont("ST-Regular", 8)
        canvas.setFillColor(MUTED)
        canvas.drawString(doc.leftMargin, height - 13 * mm, "SLEEP TIGHT | CRITICAL LITERATURE REVIEW")
        canvas.drawRightString(width - doc.rightMargin, 12 * mm, f"{page - 1}")
        canvas.setFillColor(AMBER)
        canvas.rect(doc.leftMargin, 10.5 * mm, 17 * mm, 0.8 * mm, stroke=0, fill=1)
        canvas.restoreState()

    def afterFlowable(self, flowable):
        if isinstance(flowable, Paragraph):
            level = getattr(flowable, "toc_level", None)
            if level is not None:
                text = flowable.getPlainText()
                key = getattr(flowable, "anchor_key", None)
                self.canv.bookmarkPage(key)
                self.canv.addOutlineEntry(text, key, level=level, closed=False)
                self.notify("TOCEntry", (level, text, self.page - 1, key))


def styles():
    sample = getSampleStyleSheet()
    return {
        "cover_kicker": ParagraphStyle(
            "CoverKicker",
            parent=sample["Normal"],
            fontName="ST-Bold",
            fontSize=10,
            leading=14,
            textColor=AMBER,
            tracking=2,
            spaceAfter=10,
        ),
        "cover_title": ParagraphStyle(
            "CoverTitle",
            parent=sample["Title"],
            fontName="ST-Bold",
            fontSize=30,
            leading=35,
            textColor=WHITE,
            alignment=TA_LEFT,
            spaceAfter=14,
        ),
        "cover_subtitle": ParagraphStyle(
            "CoverSubtitle",
            parent=sample["Normal"],
            fontName="ST-Regular",
            fontSize=15,
            leading=21,
            textColor=colors.HexColor("#DCE8F0"),
            spaceAfter=28,
        ),
        "cover_meta": ParagraphStyle(
            "CoverMeta",
            parent=sample["Normal"],
            fontName="ST-Regular",
            fontSize=10,
            leading=16,
            textColor=colors.HexColor("#B9C9D4"),
        ),
        "h1": ParagraphStyle(
            "H1",
            parent=sample["Heading1"],
            fontName="ST-Bold",
            fontSize=21,
            leading=25,
            textColor=NAVY,
            spaceBefore=7 * mm,
            spaceAfter=3.5 * mm,
            keepWithNext=True,
        ),
        "h2": ParagraphStyle(
            "H2",
            parent=sample["Heading2"],
            fontName="ST-Bold",
            fontSize=14,
            leading=18,
            textColor=MID_BLUE,
            spaceBefore=5 * mm,
            spaceAfter=2.2 * mm,
            keepWithNext=True,
        ),
        "body": ParagraphStyle(
            "Body",
            parent=sample["BodyText"],
            fontName="ST-Regular",
            fontSize=9.4,
            leading=13.5,
            textColor=INK,
            spaceAfter=2.5 * mm,
            alignment=TA_LEFT,
            splitLongWords=False,
        ),
        "bullet": ParagraphStyle(
            "Bullet",
            parent=sample["BodyText"],
            fontName="ST-Regular",
            fontSize=9.2,
            leading=13.2,
            leftIndent=6 * mm,
            firstLineIndent=-3.5 * mm,
            bulletIndent=1.5 * mm,
            textColor=INK,
            spaceAfter=1.2 * mm,
        ),
        "quote": ParagraphStyle(
            "Quote",
            parent=sample["BodyText"],
            fontName="ST-Italic",
            fontSize=11,
            leading=16,
            textColor=NAVY,
            leftIndent=8 * mm,
            rightIndent=8 * mm,
            spaceBefore=3 * mm,
            spaceAfter=4 * mm,
        ),
        "table_head": ParagraphStyle(
            "TableHead",
            parent=sample["Normal"],
            fontName="ST-Bold",
            fontSize=7.4,
            leading=9.3,
            textColor=WHITE,
        ),
        "table_body": ParagraphStyle(
            "TableBody",
            parent=sample["Normal"],
            fontName="ST-Regular",
            fontSize=7.1,
            leading=9.2,
            textColor=INK,
        ),
        "small": ParagraphStyle(
            "Small",
            parent=sample["Normal"],
            fontName="ST-Regular",
            fontSize=7.8,
            leading=10.5,
            textColor=MUTED,
        ),
        "toc_title": ParagraphStyle(
            "TOCTitle",
            parent=sample["Heading1"],
            fontName="ST-Bold",
            fontSize=22,
            leading=26,
            textColor=NAVY,
            spaceAfter=7 * mm,
        ),
        "callout": ParagraphStyle(
            "Callout",
            parent=sample["BodyText"],
            fontName="ST-Bold",
            fontSize=11,
            leading=16,
            textColor=NAVY,
            leftIndent=6 * mm,
            rightIndent=6 * mm,
            spaceBefore=3 * mm,
            spaceAfter=3 * mm,
        ),
    }


def inline_markup(text: str) -> str:
    text = html.escape(text, quote=False)
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"(?<!\*)\*([^*]+?)\*(?!\*)", r"<i>\1</i>", text)
    text = re.sub(r"`([^`]+)`", r"<font name='ST-Bold'>\1</font>", text)
    url_re = re.compile(r"(https?://[^\s<]+)")

    def linkify(match):
        url = match.group(1)
        trail = ""
        while url and url[-1] in ".,;:)":
            trail = url[-1] + trail
            url = url[:-1]
        return f"<link href='{url}' color='#355E78'><u>{url}</u></link>{trail}"

    return url_re.sub(linkify, text)


def paragraph(text, style, **attrs):
    p = Paragraph(inline_markup(text.strip()), style)
    for key, value in attrs.items():
        setattr(p, key, value)
    return p


def parse_table(lines, st, width):
    rows = []
    for line in lines:
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if all(re.fullmatch(r":?-{3,}:?", c or "") for c in cells):
            continue
        rows.append(cells)
    if not rows:
        return Spacer(1, 1)
    cols = max(len(r) for r in rows)
    rows = [r + [""] * (cols - len(r)) for r in rows]
    data = []
    for ri, row in enumerate(rows):
        style = st["table_head"] if ri == 0 else st["table_body"]
        data.append([Paragraph(inline_markup(cell), style) for cell in row])
    if cols == 4:
        col_widths = [width * 0.16, width * 0.31, width * 0.17, width * 0.36]
    elif cols == 3:
        col_widths = [width * 0.22, width * 0.39, width * 0.39]
    else:
        col_widths = [width / cols] * cols
    table = Table(data, colWidths=col_widths, repeatRows=1, hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), NAVY),
                ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("GRID", (0, 0), (-1, -1), 0.35, LIGHT_LINE),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, PALE_BLUE]),
            ]
        )
    )
    return table


def build_story(markdown: str, st, doc_width):
    lines = markdown.splitlines()
    story = []

    # Cover
    story.extend(
        [
            Spacer(1, 30 * mm),
            Paragraph("SLEEP TIGHT RESEARCH SERIES", st["cover_kicker"]),
            Paragraph("Designing a Wearable-Adaptive Sleep Environment", st["cover_title"]),
            Paragraph(
                "A critical literature review of evening light, consumer sleep sensing, music, and broadband sound",
                st["cover_subtitle"],
            ),
            HRFlowable(width="42%", thickness=2, color=AMBER, hAlign="LEFT", spaceAfter=12 * mm),
            Paragraph("Prepared for the Sleep Tight project", st["cover_meta"]),
            Paragraph("Structured critical narrative review", st["cover_meta"]),
            Paragraph("Evidence current through 15 July 2026", st["cover_meta"]),
            Spacer(1, 48 * mm),
            Paragraph(
                "LIGHT  /  WEARABLES  /  MUSIC  /  BROADBAND SOUND",
                st["cover_kicker"],
            ),
            PageBreak(),
        ]
    )

    # TOC
    story.append(Paragraph("Contents", st["toc_title"]))
    toc = TableOfContents()
    toc.levelStyles = [
        ParagraphStyle(
            "TOC1",
            fontName="ST-Bold",
            fontSize=10,
            leading=15,
            leftIndent=0,
            firstLineIndent=0,
            textColor=NAVY,
            spaceBefore=2,
        ),
        ParagraphStyle(
            "TOC2",
            fontName="ST-Regular",
            fontSize=8.5,
            leading=12,
            leftIndent=8 * mm,
            firstLineIndent=0,
            textColor=MUTED,
        ),
    ]
    story.extend([toc, PageBreak()])

    # Skip document title/subtitle/metadata block before Abstract.
    start = next(i for i, line in enumerate(lines) if line.strip() == "## Abstract")
    lines = lines[start:]
    i = 0
    heading_count = 0
    paragraph_buffer = []

    def flush_paragraph():
        nonlocal paragraph_buffer
        if paragraph_buffer:
            text = " ".join(part.strip() for part in paragraph_buffer).strip()
            if text:
                story.append(paragraph(text, st["body"]))
            paragraph_buffer = []

    while i < len(lines):
        raw = lines[i]
        line = raw.strip()
        if not line:
            flush_paragraph()
            i += 1
            continue
        if line == "---":
            flush_paragraph()
            story.append(HRFlowable(width="100%", thickness=0.6, color=LIGHT_LINE, spaceBefore=3 * mm, spaceAfter=3 * mm))
            i += 1
            continue
        if line.startswith("|"):
            flush_paragraph()
            block = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                block.append(lines[i])
                i += 1
            story.extend([Spacer(1, 2 * mm), parse_table(block, st, doc_width), Spacer(1, 3 * mm)])
            continue
        if line.startswith("## ") or line.startswith("### "):
            flush_paragraph()
            level = 0 if line.startswith("## ") else 1
            text = line[3:] if level == 0 else line[4:]
            heading_count += 1
            key = f"section_{heading_count}"
            p = Paragraph(f"<a name='{key}'/>{inline_markup(text)}", st["h1"] if level == 0 else st["h2"])
            p.toc_level = level
            p.anchor_key = key
            if level == 0 and text in {"3. Light: from visual ambience to circadian dose", "4. What a smartwatch can and cannot know about sleep", "5. Music and sound", "6. Integrated control design", "7. Evidence quality summary", "8. Research gaps and proposed validation", "9. Final answer", "References", "Appendix A. Peer-review and source-status guide", "Appendix B. Measurement checklist"}:
                if story and not isinstance(story[-1], PageBreak):
                    story.append(PageBreak())
            story.append(p)
            i += 1
            continue
        if re.match(r"^\d+\.\s+", line):
            flush_paragraph()
            num, text = line.split(". ", 1)
            story.append(Paragraph(inline_markup(text), st["bullet"], bulletText=f"{num}."))
            i += 1
            continue
        if line.startswith("- "):
            flush_paragraph()
            story.append(Paragraph(inline_markup(line[2:]), st["bullet"], bulletText="•"))
            i += 1
            continue
        if line.startswith("> "):
            flush_paragraph()
            quote = line[2:]
            story.append(
                Table(
                    [[Paragraph(inline_markup(quote), st["quote"])]],
                    colWidths=[doc_width],
                    style=TableStyle(
                        [
                            ("BACKGROUND", (0, 0), (-1, -1), PALE_AMBER),
                            ("BOX", (0, 0), (-1, -1), 0.6, AMBER),
                            ("LEFTPADDING", (0, 0), (-1, -1), 5),
                            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                        ]
                    ),
                )
            )
            i += 1
            continue
        paragraph_buffer.append(line)
        i += 1
    flush_paragraph()
    return story


def append_evidence_matrix(story, st, doc_width):
    story.append(PageBreak())
    key = "appendix_c"
    p = Paragraph(f"<a name='{key}'/>Appendix C. Study-by-study evidence matrix", st["h1"])
    p.toc_level = 0
    p.anchor_key = key
    story.append(p)
    story.append(
        Paragraph(
            "Peer-reviewed status describes the publication process, not the strength of the evidence. Quality reflects design, directness, consistency, precision, and relevance to Sleep Tight.",
            st["body"],
        )
    )
    with MATRIX.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))

    data = [[
        Paragraph("Study / design", st["table_head"]),
        Paragraph("Peer review", st["table_head"]),
        Paragraph("Evidence judgement", st["table_head"]),
        Paragraph("Decision", st["table_head"]),
    ]]
    for row in rows:
        study = f"<b>{html.escape(row['Study'])} ({row['Year']})</b><br/>{html.escape(row['Domain'])}; {html.escape(row['Design'])}; n={html.escape(row['Sample'])}<br/><link href='{row['URL']}' color='#355E78'>Source</link>"
        data.append([
            Paragraph(study, st["table_body"]),
            Paragraph(html.escape(row["Peer_reviewed"]), st["table_body"]),
            Paragraph(f"<b>{html.escape(row['Quality'])}</b><br/>{html.escape(row['Key_result'])}", st["table_body"]),
            Paragraph(html.escape(row["Product_decision"]), st["table_body"]),
        ])
    table = Table(
        data,
        colWidths=[doc_width * 0.29, doc_width * 0.11, doc_width * 0.36, doc_width * 0.24],
        repeatRows=1,
        hAlign="LEFT",
    )
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), NAVY),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("GRID", (0, 0), (-1, -1), 0.35, LIGHT_LINE),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, PALE_BLUE]),
            ]
        )
    )
    story.append(table)


def main() -> None:
    register_fonts()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    st = styles()
    doc = ReviewDocTemplate(
        str(OUTPUT),
        pagesize=A4,
        leftMargin=19 * mm,
        rightMargin=19 * mm,
        topMargin=24 * mm,
        bottomMargin=19 * mm,
        title="Designing a Wearable-Adaptive Sleep Environment",
        author="Sleep Tight Research",
        subject="Critical literature review of light, wearable sleep sensing, music, and broadband sound",
    )
    story = build_story(SOURCE.read_text(encoding="utf-8"), st, doc.width)
    append_evidence_matrix(story, st, doc.width)
    doc.multiBuild(story)
    print(OUTPUT)


if __name__ == "__main__":
    main()
