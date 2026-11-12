"""python -m extractor samples/*.pdf --out out/ [--provider mock|anthropic|openai]"""

from __future__ import annotations

import argparse
from pathlib import Path

from .export import write_erp_csv, write_review_xlsx
from .extract import extract, rule_based
from .llm import LLMClient
from .model import validate


def main() -> None:
    p = argparse.ArgumentParser(description="Health-plan invoice PDFs -> validated ERP import files")
    p.add_argument("pdfs", nargs="+", type=Path)
    p.add_argument("--out", type=Path, default=Path("out"))
    p.add_argument("--provider", default=None, help="mock (default, rule-based), anthropic or openai")
    p.add_argument("--model", default=None)
    a = p.parse_args()

    client = LLMClient(a.provider, a.model, mock_fn=rule_based)
    a.out.mkdir(parents=True, exist_ok=True)
    invoices = []
    for pdf in a.pdfs:
        inv = validate(extract(pdf, client))
        invoices.append(inv)
        if inv.ok:
            csv_path = write_erp_csv(inv, a.out / f"{pdf.stem}_erp.csv")
            print(f"[READY]        {pdf.name}: {len(inv.lines)} lines -> {csv_path}")
        else:
            print(f"[NEEDS REVIEW] {pdf.name}: not exported")
            for issue in inv.issues:
                print(f"               - {issue}")
    review = write_review_xlsx(invoices, a.out / "review.xlsx")
    print(f"Review workbook: {review}")


if __name__ == "__main__":
    main()
