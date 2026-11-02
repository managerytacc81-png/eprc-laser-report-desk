"""Unit tests for Customer Intake & Form FDA 3632 Report Generator."""

import pytest
from pathlib import Path
import sys

desk_dir = Path(__file__).resolve().parent.parent
if str(desk_dir) not in sys.path:
    sys.path.insert(0, str(desk_dir))

from report_intake import (
    LaserProductIntake, validate_intake_compliance,
    generate_markdown_report, generate_pdf_report, create_sample_intake
)

def test_intake_dataclass_serialization():
    sample = create_sample_intake()
    d = sample.to_dict()
    assert d["product_name"] == sample.product_name
    assert d["laser_class"] == "Class IV"
    assert len(d["model_family"]) >= 3

    recreated = LaserProductIntake.from_dict(d)
    assert recreated.product_name == sample.product_name
    assert recreated.emission_wavelengths == sample.emission_wavelengths

def test_validate_intake_compliant():
    sample = create_sample_intake()
    val = validate_intake_compliance(sample)
    assert val["compliant"] is True
    assert len(val["issues"]) == 0

def test_validate_intake_missing_class_iv_features():
    sample = create_sample_intake()
    sample.has_key_control = False
    sample.has_remote_interlock_connector = False

    val = validate_intake_compliance(sample)
    assert val["compliant"] is False
    assert any("Key Control" in issue for issue in val["issues"])
    assert any("Remote Interlock" in issue for issue in val["issues"])

def test_validate_surveying_laser_notice_54():
    sample = create_sample_intake()
    sample.product_name = "Surveying Laser Level Pro"
    sample.laser_class = "Class IV"

    val = validate_intake_compliance(sample)
    assert val["compliant"] is False
    assert any("Laser Notice 54" in issue for issue in val["issues"])

def test_generate_markdown_report():
    sample = create_sample_intake()
    md = generate_markdown_report(sample)
    assert f"# Radiation Safety Product Report of {sample.product_name}" in md
    assert "FORM FDA 3632" in md
    assert "21 CFR 1002.10" in md
    assert "RadHealthCustomerService@fda.hhs.gov" in md
    assert sample.manufacturer_name in md
    assert "Part 4: Engineering Safety Features" in md
    assert "Part 5: Labeling, Warning Logotypes, and Certification" in md

def test_generate_pdf_report(tmp_path):
    sample = create_sample_intake()
    pdf_out = tmp_path / "test_report_3632.pdf"
    generate_pdf_report(sample, pdf_out)
    assert pdf_out.exists()
    assert pdf_out.stat().st_size > 3000
