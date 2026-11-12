"""PDF -> text -> structured invoice.

Two strategies:
- LLM extraction (anthropic / openai): works across different operators' layouts.
- Rule-based parser (mock / demo mode): fast and free for a known layout.
Both produce the same Invoice object, and both go through the same validation.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pdfplumber

from .llm import LLMClient
from .model import Invoice, Line, brl

SYSTEM = (
    "You extract data from Brazilian health-plan invoices. Return ONLY valid JSON, no prose, "
    "with this shape: {\"operator\": str, \"invoice_number\": str, \"reference\": \"MM/YYYY\", "
    "\"invoice_total\": str, \"lines\": [{\"employee_code\": str, \"beneficiary\": str, "
    "\"relationship\": str, \"plan\": str, \"monthly_fee\": str, \"copay\": str, \"total\": str}]}. "
    "Copy amounts exactly as printed (Brazilian format, e.g. '1.234,56'). Do not compute or "
    "correct anything: if a value looks wrong, copy it as printed."
)

ROW = re.compile(
    r"^(E\d{4})\s+(.+?)\s+(Holder|Spouse|Child|Dependent)\s+(\S+)\s+"
    r"([\d.]+,\d{2})\s+([\d.]+,\d{2})\s+([\d.]+,\d{2})$"
)


def pdf_text(path: Path) -> str:
    with pdfplumber.open(path) as pdf:
        return "\n".join(page.extract_text() or "" for page in pdf.pages)


def rule_based(_system: str, prompt: str) -> str:
    """Demo-mode 'model': parses the known sample layout with regular expressions."""
    text = prompt.split("INVOICE TEXT:", 1)[1]
    find = lambda pat: (re.search(pat, text) or [None, ""])[1]  # noqa: E731
    lines = []
    for raw in text.splitlines():
        m = ROW.match(raw.strip())
        if m:
            code, name, rel, plan, fee, copay, total = m.groups()
            lines.append(dict(employee_code=code, beneficiary=name, relationship=rel, plan=plan,
                              monthly_fee=fee, copay=copay, total=total))
    return json.dumps({
        "operator": text.strip().splitlines()[0].strip(),
        "invoice_number": find(r"Invoice number:\s*(\S+)"),
        "reference": find(r"Reference:\s*(\d{2}/\d{4})"),
        "invoice_total": find(r"Invoice total:\s*R\$\s*([\d.]+,\d{2})"),
        "lines": lines,
    })


def _json_block(raw: str) -> dict:
    start, end = raw.find("{"), raw.rfind("}")
    if start < 0 or end < 0:
        raise ValueError("Model did not return JSON.")
    return json.loads(raw[start:end + 1])


def extract(path: Path, client: LLMClient) -> Invoice:
    text = pdf_text(path)
    data = _json_block(client.complete(SYSTEM, "INVOICE TEXT:\n" + text, max_tokens=3000))
    return Invoice(
        source_file=path.name,
        operator=data.get("operator", ""),
        invoice_number=data.get("invoice_number", ""),
        reference=data.get("reference", ""),
        invoice_total=brl(data.get("invoice_total") or "0"),
        lines=[
            Line(
                employee_code=l["employee_code"], beneficiary=l["beneficiary"],
                relationship=l["relationship"], plan=l["plan"],
                monthly_fee=brl(l["monthly_fee"]), copay=brl(l["copay"]), total=brl(l["total"]),
            )
            for l in data.get("lines", [])
        ],
    )


__all__ = ["extract", "pdf_text", "rule_based"]
