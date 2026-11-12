"""Data model and validation. Every extracted invoice is checked before export."""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal as D
from typing import List


def brl(text: str) -> D:
    """'2.552,30' -> Decimal('2552.30')"""
    return D(str(text).replace("R$", "").strip().replace(".", "").replace(",", "."))


@dataclass
class Line:
    employee_code: str
    beneficiary: str
    relationship: str
    plan: str
    monthly_fee: D
    copay: D
    total: D


@dataclass
class Invoice:
    source_file: str
    operator: str
    invoice_number: str
    reference: str          # MM/YYYY
    invoice_total: D
    lines: List[Line]
    issues: List[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.issues


def validate(inv: Invoice) -> Invoice:
    inv.issues.clear()
    if not inv.lines:
        inv.issues.append("No beneficiary lines found.")
    for i, ln in enumerate(inv.lines, start=1):
        if ln.monthly_fee + ln.copay != ln.total:
            inv.issues.append(
                f"Line {i} ({ln.beneficiary}): fee {ln.monthly_fee} + co-pay {ln.copay} != total {ln.total}.")
        if not ln.employee_code:
            inv.issues.append(f"Line {i} ({ln.beneficiary}): missing employee code.")
    computed = sum((ln.monthly_fee + ln.copay for ln in inv.lines), D("0"))
    if computed != inv.invoice_total:
        inv.issues.append(f"Invoice total {inv.invoice_total} != sum of fee + co-pay {computed}.")
    return inv
