from decimal import Decimal as D
from pathlib import Path

from extractor.export import payroll_entries, write_erp_csv
from extractor.extract import extract, rule_based
from extractor.llm import LLMClient
from extractor.model import brl, validate

SAMPLES = Path(__file__).parents[1] / "samples"
CLIENT = LLMClient("mock", mock_fn=rule_based)


def test_brl_parsing():
    assert brl("2.552,30") == D("2552.30")
    assert brl("R$ 0,00") == D("0.00")


def test_clean_invoice_is_ready():
    inv = validate(extract(SAMPLES / "vitalis_invoice_2026_10.pdf", CLIENT))
    assert inv.ok, inv.issues
    assert inv.invoice_number == "2026-1045"
    assert inv.reference == "10/2026"
    assert len(inv.lines) == 5
    assert inv.invoice_total == D("2552.30")


def test_invoice_with_error_is_blocked():
    inv = validate(extract(SAMPLES / "vitalis_invoice_2026_11_with_error.pdf", CLIENT))
    assert not inv.ok
    assert any("Fernanda Alves" in i for i in inv.issues)
    assert any(i.startswith("Invoice total") for i in inv.issues)


def test_dependents_are_charged_to_the_holder():
    inv = validate(extract(SAMPLES / "vitalis_invoice_2026_10.pdf", CLIENT))
    entries = {(emp, ev): amt for emp, ev, _, amt in payroll_entries(inv)}
    assert entries[("E1023", "9201")] == D("412.30") + D("198.40")
    assert entries[("E1041", "9202")] == D("120.50")


def test_erp_csv_format(tmp_path):
    inv = validate(extract(SAMPLES / "vitalis_invoice_2026_10.pdf", CLIENT))
    lines = write_erp_csv(inv, tmp_path / "erp.csv").read_text().splitlines()
    assert lines[0] == "employee_code;event_code;reference;amount"
    assert "E1023;9201;10/2026;610,70" in lines
