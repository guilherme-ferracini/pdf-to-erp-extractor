# PDF to ERP Extractor

[![tests](https://github.com/guilherme-ferracini/pdf-to-erp-extractor/actions/workflows/tests.yml/badge.svg)](https://github.com/guilherme-ferracini/pdf-to-erp-extractor/actions)

Reads **health-plan invoices in PDF**, extracts every beneficiary line with an LLM (Claude or OpenAI), **validates the totals** and writes a **payroll import file** for the accounting ERP, plus a review workbook for the team.

## Why this exists

At the accounting firm where I lead automation, client companies send their health-plan invoices as PDFs every month. The team used to retype each one into a spreadsheet, line by line, to feed the payroll system. That step was 100% manual, slow and error-prone.

The production module now does it with AI. This repo is a clean, standalone rewrite with **fictional invoices**, showing the design:

- **LLM for reading, code for checking.** The model only copies what is printed. Python then verifies that each line's fee + co-pay equals its total and that the lines add up to the invoice total.
- **Nothing wrong reaches the ERP.** An invoice with any inconsistency is blocked and flagged in red in the review workbook, so a person looks at it before payroll runs.
- **Same output, any strategy.** LLM extraction handles different operators' layouts. A rule-based parser (demo mode) handles a known layout for free. Both produce the same `Invoice` object and go through the same validation.

## Pipeline

```
invoice.pdf ──► pdfplumber (text) ──► LLM or rules (JSON) ──► validate ──┬─► READY: ERP import .csv
                                                                          └─► NEEDS REVIEW: blocked
                                                    all invoices ──► review.xlsx (lines + summary)
```

## Quickstart

```bash
pip install -r requirements.txt

# Demo mode: rule-based parser, no API key needed
python -m extractor samples/*.pdf --out out/

# LLM extraction (works across layouts)
export LLM_PROVIDER=anthropic ANTHROPIC_API_KEY=...      # or openai
python -m extractor samples/*.pdf --out out/
```

```
[READY]        vitalis_invoice_2026_10.pdf: 5 lines -> out/vitalis_invoice_2026_10_erp.csv
[NEEDS REVIEW] vitalis_invoice_2026_11_with_error.pdf: not exported
               - Line 3 (Carlos Lima): fee 655.90 + co-pay 45.00 != total 710.90.
               - Line 5 (Fernanda Alves): fee 412.30 + co-pay 0.00 != total 421.30.
               - Invoice total 2416.80 != sum of fee + co-pay 2397.80.
Review workbook: out/review.xlsx
```

The second sample invoice carries deliberate errors to show the validation working.

## ERP import format

```
employee_code;event_code;reference;amount
E1023;9201;10/2026;610,70
E1023;9202;10/2026;35,00
```

- Dependents are charged to the holder's employee code.
- `9201` (monthly fee) and `9202` (co-payment) are example event codes: map them to your payroll events in `extractor/export.py`.

## Project layout

```
extractor/
  extract.py   PDF text + LLM / rule-based extraction
  model.py     data model and validation
  export.py    ERP CSV and review workbook
  llm.py       provider-agnostic client (anthropic | openai | mock)
samples/       fictional invoices and generated output
scripts/       make_samples.py regenerates the sample PDFs
tests/         pytest suite
```

## Tests

```bash
python -m pytest -q
```

## License

MIT
