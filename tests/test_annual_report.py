"""Unit tests for Form FDA 3636 Annual Report Generator."""

import pytest
from datetime import date
from pathlib import Path
import sys

desk_dir = Path(__file__).resolve().parent.parent
if str(desk_dir) not in sys.path:
    sys.path.insert(0, str(desk_dir))

from annual_report import (
    AnnualReportIntake, LaserModelProduction,
    compute_reporting_period, generate_markdown_annual_report,
    generate_pdf_annual_report, create_sample_annual_report_intake
)

def test_compute_reporting_period_2026():
    # If today is November 2, 2026, the period ending June 30, 2026 was due Sept 1, 2026 (Overdue)
    ref = date(2026, 11, 2)
    period = compute_reporting_period(report_year=2026, ref_date=ref)
    assert period["period_string"] == "July 1, 2025 through June 30, 2026"
    assert "September 01, 2026" in period["filing_deadline"]
    assert period["is_overdue"] is True
    assert "OVERDUE" in period["status_flag"]

def test_compute_reporting_period_future():
    # If filing for 2027 early (e.g. in May 2027 before Sept 1 deadline)
    ref = date(2027, 5, 1)
    period = compute_reporting_period(report_year=2027, ref_date=ref)
    assert period["period_string"] == "July 1, 2026 through June 30, 2027"
    assert period["is_overdue"] is False
    assert "ON TIME" in period["status_flag"]

def test_generate_markdown_annual_report():
    sample = create_sample_annual_report_intake(report_year=2026)
    ref = date(2026, 11, 2)
    period = compute_reporting_period(report_year=2026, ref_date=ref)
    md = generate_markdown_annual_report(sample, period)

    assert f"# Radiation Safety Annual Report of {sample.manufacturer_name}" in md
    assert "FORM FDA 3636" in md
    assert "21 CFR 1002.13" in md
    assert "September 01, 2026" in md
    assert "2210452-000" in md  # accession number
    assert "7,400 units" in md  # total units tested

def test_generate_pdf_annual_report(tmp_path):
    sample = create_sample_annual_report_intake(report_year=2026)
    period = compute_reporting_period(report_year=2026)
    pdf_out = tmp_path / "test_annual_report_3636.pdf"
    generate_pdf_annual_report(sample, period, pdf_out)
    assert pdf_out.exists()
    assert pdf_out.stat().st_size > 3000
