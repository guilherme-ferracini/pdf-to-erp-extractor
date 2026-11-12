"""Generates the fictional health-plan invoices in samples/ (requires reportlab)."""

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

OUT = Path(__file__).parents[1] / "samples"

INVOICES = {
    "vitalis_invoice_2026_10.pdf": {
        "number": "2026-1045", "reference": "10/2026",
        "rows": [
            ("E1023", "Maria Souza", "Holder", "Ward", "412,30", "35,00", "447,30"),
            ("E1023", "Pedro Souza", "Child", "Ward", "198,40", "0,00", "198,40"),
            ("E1041", "Carlos Lima", "Holder", "Private", "655,90", "120,50", "776,40"),
            ("E1041", "Julia Lima", "Spouse", "Private", "655,90", "0,00", "655,90"),
            ("E1057", "Fernanda Alves", "Holder", "Ward", "412,30", "62,00", "474,30"),
        ],
        "total": "2.552,30",
    },
    # Second invoice carries deliberate errors (two row totals) to show validation
    "vitalis_invoice_2026_11_with_error.pdf": {
        "number": "2026-1188", "reference": "11/2026",
        "rows": [
            ("E1023", "Maria Souza", "Holder", "Ward", "412,30", "0,00", "412,30"),
            ("E1023", "Pedro Souza", "Child", "Ward", "198,40", "18,00", "216,40"),
            ("E1041", "Carlos Lima", "Holder", "Private", "655,90", "45,00", "710,90"),
            ("E1041", "Julia Lima", "Spouse", "Private", "655,90", "0,00", "655,90"),
            ("E1057", "Fernanda Alves", "Holder", "Ward", "412,30", "0,00", "421,30"),
        ],
        "total": "2.416,80",
    },
}


def build(name: str, inv: dict) -> None:
    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(str(OUT / name), pagesize=A4, title="Health plan invoice (fictional)")
    header = ["Employee code", "Beneficiary", "Relationship", "Plan", "Monthly fee", "Co-payment", "Total"]
    table = Table([header, *inv["rows"]], repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f4e79")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("ALIGN", (4, 1), (-1, -1), "RIGHT"),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
    ]))
    doc.build([
        Paragraph("VITALIS SAUDE (fictional operator)", styles["Title"]),
        Paragraph("Health plan invoice", styles["Heading2"]),
        Paragraph("Contract holder: Aurora Distribuidora Ltda (fictional)", styles["Normal"]),
        Paragraph(f"Invoice number: {inv['number']}", styles["Normal"]),
        Paragraph(f"Reference: {inv['reference']}", styles["Normal"]),
        Spacer(1, 12),
        table,
        Spacer(1, 12),
        Paragraph(f"Invoice total: R$ {inv['total']}", styles["Heading3"]),
    ])


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    for name, inv in INVOICES.items():
        build(name, inv)
        print("wrote", OUT / name)
