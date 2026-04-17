# -*- coding: utf-8 -*-
"""Generate EchoMie-测试报告.docx from docs/EchoMie-测试报告.md (requires python-docx)."""
import re
from pathlib import Path

from docx import Document
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn


def set_cell_font(cell, size_pt=9):
    for p in cell.paragraphs:
        for r in p.runs:
            r.font.size = Pt(size_pt)
            r.font.name = "宋体"
            r._element.rPr.rFonts.set(qn("w:eastAsia"), "宋体")


def add_table_from_rows(doc, rows):
    if not rows:
        return
    ncols = max(len(r) for r in rows)
    tbl = doc.add_table(rows=len(rows), cols=ncols)
    tbl.style = "Table Grid"
    for i, row in enumerate(rows):
        for j, text in enumerate(row):
            if j < ncols:
                cell = tbl.rows[i].cells[j]
                cell.text = text.strip()
                set_cell_font(cell, 9 if i > 0 else 10)
    doc.add_paragraph()


def _is_md_table_separator(parts):
    if not parts:
        return False
    return all(p and set(p) <= set("-:") for p in parts)


def parse_md_table(lines, start_idx):
    rows = []
    i = start_idx
    while i < len(lines):
        line = lines[i].strip()
        if not line.startswith("|"):
            break
        parts = [p.strip() for p in line.split("|")]
        parts = [p for p in parts if p != ""]
        if _is_md_table_separator(parts):
            i += 1
            continue
        rows.append(parts)
        i += 1
    return rows, i


def main():
    root = Path(__file__).resolve().parent
    md_path = root / "docs" / "EchoMie-测试报告.md"
    out_path = root / "docs" / "EchoMie-测试报告.docx"

    text = md_path.read_text(encoding="utf-8")
    lines = text.splitlines()

    doc = Document()
    sect = doc.sections[0]
    sect.top_margin = Cm(2)
    sect.bottom_margin = Cm(2)
    sect.left_margin = Cm(2.5)
    sect.right_margin = Cm(2.5)

    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if stripped.startswith("# "):
            p = doc.add_paragraph(stripped[2:].strip())
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            for r in p.runs:
                r.bold = True
                r.font.size = Pt(18)
                r.font.name = "黑体"
                r._element.rPr.rFonts.set(qn("w:eastAsia"), "黑体")
            i += 1
            continue

        if stripped.startswith("## "):
            doc.add_heading(stripped[3:].strip(), level=1)
            i += 1
            continue

        if stripped.startswith("### "):
            doc.add_heading(stripped[4:].strip(), level=2)
            i += 1
            continue

        if stripped == "---":
            i += 1
            continue

        if stripped.startswith("|"):
            rows, ni = parse_md_table(lines, i)
            if rows:
                add_table_from_rows(doc, rows)
            i = ni
            continue

        if stripped.startswith("- "):
            doc.add_paragraph(stripped[2:].strip(), style="List Bullet")
            i += 1
            continue
        if re.match(r"^\d+\.\s", stripped):
            body = re.sub(r"^\d+\.\s*", "", stripped).replace("**", "")
            doc.add_paragraph(body, style="List Number")
            i += 1
            continue

        if stripped.startswith("**") and stripped.endswith("**"):
            p = doc.add_paragraph(stripped.strip("*"))
            for r in p.runs:
                r.bold = True
            i += 1
            continue

        if stripped:
            doc.add_paragraph(stripped)
        i += 1

    doc.save(out_path)
    print("Saved:", out_path)


if __name__ == "__main__":
    main()
