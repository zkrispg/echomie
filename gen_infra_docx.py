# -*- coding: utf-8 -*-
"""Generate EchoMie-前期基础设施与合规准备.docx (requires python-docx)."""
from pathlib import Path

from gen_test_report_docx import build_document_from_md_file


def main():
    root = Path(__file__).resolve().parent
    build_document_from_md_file(
        root / "docs" / "EchoMie-前期基础设施与合规准备.md",
        root / "docs" / "EchoMie-前期基础设施与合规准备.docx",
    )


if __name__ == "__main__":
    main()
