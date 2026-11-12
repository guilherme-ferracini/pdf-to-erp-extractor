"""Exports validated invoices to an ERP payroll-import file and a review workbook.

The ERP layout below is a generic `employee;event;reference;amount` file, the
kind most Brazilian payroll systems accept through a configurable import.
Event codes are examples: map them to your own payroll events in EVENTS.
"""

from __future__ import annotations

from collections import defaultdict
from decimal import Decimal as D
from pathlib import Path
from typing import Dict, List, Tuple

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill

from .model import Invoice

EVENTS = {"monthly_fee": "9201", "copay": "9202"}   # example payroll event codes


def payroll_entries(inv: Invoice) -> List[Tuple[str, str, str, D]]:
    """Dependents are charged to the holder's employee code."""
    totals: Dict[Tuple[str, str], D] = defaultdict(lambda: D("0"))
    for ln in inv.lines:
        totals[(ln.employee_code, EVENTS["monthly_fee"])] += ln.monthly_fee
        if ln.copay:
            totals[(ln.employee_code, EVENTS["copay"])] += ln.copay
    return [(emp, ev, inv.reference, amt) for (emp, ev), amt in sorted(totals.items())]


def write_erp_csv(inv: Invoice, path: Path) -> Path:
    rows = ["employee_code;event_code;reference;amount"]
    for emp, ev, ref, amt in payroll_entries(inv):
        rows.append(f"{emp};{ev};{ref};{str(amt).replace('.', ',')}")
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")
    return path


def write_review_xlsx(invoices: List[Invoice], path: Path) -> Path:
    wb = Workbook()
    ws = wb.active
    ws.title = "Lines"
    header = ["File", "Invoice", "Reference", "Employee code", "Beneficiary", "Relationship",
              "Plan", "Monthly fee", "Co-payment", "Total", "Line check"]
    ws.append(header)
    red = PatternFill("solid", fgColor="F8D7DA")
    for inv in invoices:
        for ln in inv.lines:
            ok = ln.monthly_fee + ln.copay == ln.total
            ws.append([inv.source_file, inv.invoice_number, inv.reference, ln.employee_code, ln.beneficiary,
                       ln.relationship, ln.plan, float(ln.monthly_fee), float(ln.copay), float(ln.total),
                       "OK" if ok else "CHECK"])
            if not ok:
                for cell in ws[ws.max_row]:
                    cell.fill = red

    summary = wb.create_sheet("Summary")
    summary.append(["File", "Invoice", "Reference", "Invoice total", "Status", "Issues"])
    for inv in invoices:
        summary.append([inv.source_file, inv.invoice_number, inv.reference, float(inv.invoice_total),
                        "READY" if inv.ok else "NEEDS REVIEW", " | ".join(inv.issues)])
    for sheet in (ws, summary):
        for cell in sheet[1]:
            cell.font = Font(bold=True)
        for col in sheet.columns:
            sheet.column_dimensions[col[0].column_letter].width = max(12, min(60, max(len(str(c.value or "")) for c in col) + 2))
    wb.save(path)
    return path
