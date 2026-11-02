#!/usr/bin/env python3
"""Customer Intake Questionnaire and Form FDA 3632 Radiation Safety Product Report Generator.

Takes customer intake data (product class per 21 CFR 1040.10, model family,
wavelength, power output, safety features, labels, test evidence) and generates
a completed Form FDA 3632-structured Radiation Safety Product Report draft
marked: 'Radiation Safety Product Report of <name>'.
Generates both Markdown (.md) and PDF (.pdf) formats.
"""

import os
import sys
import json
import logging
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field, asdict

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY

# Import rules knowledge base
rules_dir = Path(__file__).resolve().parent / "rules"
if str(rules_dir) not in sys.path:
    sys.path.insert(0, str(rules_dir))
try:
    from knowledge_base import get_knowledge_base
except ImportError:
    from rules.knowledge_base import get_knowledge_base

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("report_intake")

@dataclass
class LaserProductIntake:
    product_name: str
    model_family: List[str]
    brand_name: str
    manufacturer_name: str
    manufacturer_address: str
    country_of_origin: str
    contact_person: str
    contact_email: str
    contact_phone: str

    # US Designated Agent (21 CFR 1005.25 for non-US manufacturers)
    us_agent_name: str = ""
    us_agent_address: str = ""
    us_agent_phone: str = ""
    us_agent_email: str = ""

    # Technical Laser Specs
    laser_class: str = "Class IV"  # Class I, IIa, II, IIIa, IIIb, IV, Medical
    conformance_standard: str = "Laser Notice 56 / IEC 60825-1:2014 Ed. 3 & 21 CFR 1040.10"
    active_medium: str = "Semiconductor Diode"  # Diode, Fiber, CO2, Nd:YAG, DPSS
    operational_mode: str = "Continuous Wave (CW)"
    emission_wavelengths: List[str] = field(default_factory=lambda: ["450 nm"])
    max_output_power: str = "20.0 W (20,000 mW)"
    beam_divergence_mrad: str = "1.5 mrad"
    beam_diameter_aperture_mm: str = "4.0 mm"
    pulse_repetition_rate: str = "N/A (CW)"
    pulse_duration: str = "N/A (CW)"

    # Engineering Safety Features (21 CFR 1040.10(f))
    has_protective_housing: bool = True
    protective_housing_details: str = "Anodized aluminum alloy chassis enclosing optical assembly with laser-opaque viewing shield."
    has_safety_interlock: bool = True
    safety_interlock_details: str = "Dual-channel magnetic safety interlock microswitches halting emission when enclosure is opened."
    has_remote_interlock_connector: bool = True
    remote_interlock_details: str = "2-pin terminal block on rear panel allowing connection to external room/enclosure interlock loops."
    has_key_control: bool = True
    key_control_details: str = "Master physical key-switch located on front control panel; key removable only in 'OFF' position."
    has_beam_attenuator: bool = True
    beam_attenuator_details: str = "Mechanical rotary beam shutter located directly at laser diode aperture."
    has_emission_indicator: bool = True
    emission_indicator_details: str = "Bright amber LED emission warning lamp illuminated 3.0 seconds prior to and during laser emission."
    has_viewing_optics_filter: bool = True
    viewing_optics_details: str = "Enclosure inspection window certified OD 5+ at 450nm and 1064nm conforming to ANSI Z136.1."
    has_scan_failure_safeguard: bool = False
    scan_failure_details: str = "Not applicable (direct gantry translation system)."

    # Labeling & Markings (21 CFR 1040.10(g), 1010.2, 1010.3)
    has_certification_label: bool = True
    certification_label_text: str = "Complies with FDA radiation performance standards, 21 CFR 1040.10 and 1040.11 except for conformance with IEC 60825-1 Ed. 3, as described in Laser Notice No. 56, dated May 8, 2019."
    has_identification_label: bool = True
    identification_label_text: str = "Manufactured by [Firm Name], Address: [Address], Date: [MM/YYYY], Serial No: [Serial]"
    has_warning_logotype: bool = True
    warning_logotype_text: str = "DANGER - LASER RADIATION AVOID EYE OR SKIN EXPOSURE TO DIRECT OR SCATTERED RADIATION. CLASS IV LASER PRODUCT."
    has_aperture_label: bool = True
    aperture_label_text: str = "AVOID EXPOSURE - Laser radiation is emitted from this aperture."
    has_interlock_defeat_label: bool = True
    interlock_defeat_label_text: str = "CAUTION - Laser radiation when open and interlock defeated."

    # Quality Control & Testing (21 CFR 1002.30)
    incoming_inspection_protocol: str = "100% receipt verification of laser diode batches for optical output power and forward voltage."
    inline_production_test_protocol: str = "100% finished unit burn-in testing (4 hours continuous) followed by calibrated power meter check."
    test_equipment_calibrated: bool = True
    calibration_standard: str = "Thorlabs PM100D Optical Power Meter calibrated annually traceable to NIST standard."

    # User Information & Servicing (21 CFR 1040.10(h))
    user_manual_safety_section: bool = True
    user_manual_safety_details: str = "Section 1 of Operator Manual includes full radiation hazard descriptions, NOHD calculation, and protective eyewear specs."
    servicing_manual_provided: bool = True
    servicing_safety_details: str = "Field service manual specifies lockout/tagout procedures and requires OD 6+ laser safety goggles during service."

    # Submitter Attestation
    certifier_name: str = ""
    certifier_title: str = "Vice President of Quality & Regulatory Affairs"
    submission_date: str = "2026-11-02"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LaserProductIntake":
        # Filter keys to match dataclass
        valid_keys = cls.__dataclass_fields__.keys()
        filtered = {k: v for k, v in data.items() if k in valid_keys}
        return cls(**filtered)

def validate_intake_compliance(intake: LaserProductIntake) -> Dict[str, Any]:
    """Validate intake against 21 CFR 1002.1 Table 1 and 21 CFR 1040.10 requirements."""
    kb = get_knowledge_base()
    issues = []
    warnings = []

    # Check laser class requirements
    try:
        class_reqs = kb.get_class_requirements(intake.laser_class)
    except Exception as e:
        issues.append(f"Invalid laser class: {e}")
        return {"compliant": False, "issues": issues, "warnings": warnings}

    # Check Class IIIb and IV requirements
    if intake.laser_class in ["Class IIIb", "Class IV"]:
        if not intake.has_key_control:
            issues.append(f"{intake.laser_class} requires Key Control (21 CFR 1040.10(f)(4)).")
        if not intake.has_remote_interlock_connector:
            issues.append(f"{intake.laser_class} requires Remote Interlock Connector (21 CFR 1040.10(f)(3)).")
        if not intake.has_emission_indicator:
            issues.append(f"{intake.laser_class} requires Emission Indicator with delay (21 CFR 1040.10(f)(5)).")
        if not intake.has_beam_attenuator:
            issues.append(f"{intake.laser_class} requires Beam Attenuator / Shutter (21 CFR 1040.10(f)(6)).")

    # Check Class II and IIIa requirements
    if intake.laser_class in ["Class II", "Class IIIa"]:
        if not intake.has_emission_indicator:
            issues.append(f"{intake.laser_class} requires Emission Indicator (21 CFR 1040.10(f)(5)).")
        if not intake.has_beam_attenuator:
            issues.append(f"{intake.laser_class} requires Beam Attenuator (21 CFR 1040.10(f)(6)).")

    # Surveying/Leveling/Alignment (SLA) limit check per Laser Notice 54
    if any(k in intake.product_name.lower() for k in ["level", "surveying", "alignment"]):
        if intake.laser_class in ["Class IIIb", "Class IV"]:
            issues.append("Surveying, leveling, or alignment lasers must NOT exceed Class IIIa (5.0 mW) pursuant to Laser Notice 54.")

    # Labels check
    if not intake.has_certification_label:
        issues.append("Missing Certification Label (21 CFR 1010.2).")
    if not intake.has_identification_label:
        issues.append("Missing Identification Label (21 CFR 1010.3).")
    if not intake.has_warning_logotype:
        issues.append("Missing Warning Logotype Label (21 CFR 1040.10(g)).")
    if not intake.has_aperture_label:
        issues.append("Missing Aperture Warning Label (21 CFR 1040.10(g)(4)).")

    # Foreign manufacturer US agent check
    if intake.country_of_origin.upper() not in ["USA", "UNITED STATES", "US"]:
        if not intake.us_agent_name or not intake.us_agent_address:
            warnings.append("Foreign manufacturer must designate a US Agent for Service of Process pursuant to 21 CFR 1005.25.")

    return {
        "compliant": len(issues) == 0,
        "laser_class": intake.laser_class,
        "issues": issues,
        "warnings": warnings,
        "report_type_required": "Form FDA 3632 (Product Report, 21 CFR 1002.10)",
        "annual_report_required": class_reqs.get("annual_report_1002_13", True)
    }

def generate_markdown_report(intake: LaserProductIntake) -> str:
    """Generate completed Form FDA 3632 Radiation Safety Product Report draft in Markdown."""
    models_str = ", ".join(intake.model_family)
    wavelengths_str = ", ".join(intake.emission_wavelengths)
    certifier = intake.certifier_name or intake.contact_person

    md = f"""# Radiation Safety Product Report of {intake.product_name}

**Document Control:** FORM FDA 3632 (Guide for Preparing Product Reports for Lasers and Products Containing Lasers)  
**Governing Regulation:** 21 CFR 1002.10 (Electronic Product Radiation Control)  
**Submission Channel:** CDRH Radiation Health Customer Service (`RadHealthCustomerService@fda.hhs.gov`)  
**Filing Status:** Prior Product Report (Required prior to introduction into US commerce)  
**Date of Report:** {intake.submission_date}  

---

## Part 1: Identification of Manufacturer, Submitter, and US Agent

### 1.1 Manufacturer Information
- **Manufacturer Name:** {intake.manufacturer_name}
- **Physical Address:** {intake.manufacturer_address}
- **Country of Origin:** {intake.country_of_origin}
- **Brand / Trade Name:** {intake.brand_name}

### 1.2 Submitter Contact
- **Contact Person:** {intake.contact_person}
- **Title / Role:** {intake.certifier_title}
- **Email:** {intake.contact_email}
- **Telephone:** {intake.contact_phone}

### 1.3 Designated US Agent for Foreign Manufacturers (21 CFR 1005.25)
- **Designated Agent:** {intake.us_agent_name or 'N/A (US Domestic Manufacturer)'}
- **US Agent Address:** {intake.us_agent_address or 'N/A'}
- **US Agent Phone:** {intake.us_agent_phone or 'N/A'}
- **US Agent Email:** {intake.us_agent_email or 'N/A'}

---

## Part 2: Product Identification and Model Family

- **Commercial Product Name:** {intake.product_name}
- **Model Family / Numbers Covered:** {models_str}
- **Generic Product Classification:** Laser Processing & Optical Radiation System
- **FDA Product Code (PAC):** 95 R - - FE / 95 R - - DW
- **Applicable Performance Standard:** 21 CFR 1040.10 & 1040.11 / Conformance via Laser Notice 56 (IEC 60825-1:2014 Ed. 3)

---

## Part 3: Radiation Characteristics and Laser Classification

- **Laser Classification (21 CFR 1040.10):** **{intake.laser_class}**
- **Active Laser Medium:** {intake.active_medium}
- **Operating Mode:** {intake.operational_mode}
- **Operational Emission Wavelength(s):** {wavelengths_str}
- **Maximum Accessible Radiant Power:** {intake.max_output_power}
- **Beam Divergence (Full Angle):** {intake.beam_divergence_mrad}
- **Beam Diameter at Aperture:** {intake.beam_diameter_aperture_mm}
- **Pulse Duration / PRF:** {intake.pulse_duration} / {intake.pulse_repetition_rate}

---

## Part 4: Engineering Safety Features (21 CFR 1040.10(f))

| Safety Feature | 21 CFR Clause | Status | Engineering Implementation |
|---|---|---|---|
| **Protective Housing** | 1040.10(f)(1) | {'COMPLIANT' if intake.has_protective_housing else 'NON-COMPLIANT'} | {intake.protective_housing_details} |
| **Safety Interlocks** | 1040.10(f)(2) | {'COMPLIANT' if intake.has_safety_interlock else 'NON-COMPLIANT'} | {intake.safety_interlock_details} |
| **Remote Interlock Connector** | 1040.10(f)(3) | {'COMPLIANT' if intake.has_remote_interlock_connector else 'N/A'} | {intake.remote_interlock_details} |
| **Key Control** | 1040.10(f)(4) | {'COMPLIANT' if intake.has_key_control else 'N/A'} | {intake.key_control_details} |
| **Beam Attenuator / Shutter** | 1040.10(f)(6) | {'COMPLIANT' if intake.has_beam_attenuator else 'NON-COMPLIANT'} | {intake.beam_attenuator_details} |
| **Emission Indicator** | 1040.10(f)(5) | {'COMPLIANT' if intake.has_emission_indicator else 'NON-COMPLIANT'} | {intake.emission_indicator_details} |
| **Viewing Optics / Filter** | 1040.10(f)(8) | {'COMPLIANT' if intake.has_viewing_optics_filter else 'N/A'} | {intake.viewing_optics_details} |
| **Scanning Safeguard** | 1040.10(f)(10) | {'COMPLIANT' if intake.has_scan_failure_safeguard else 'N/A'} | {intake.scan_failure_details} |

---

## Part 5: Labeling, Warning Logotypes, and Certification

### 5.1 Certification Label (21 CFR 1010.2)
- **Label Status:** {'Present & Permanently Affixed' if intake.has_certification_label else 'Missing'}
- **Exact Text:** *"{intake.certification_label_text}"*

### 5.2 Identification Label (21 CFR 1010.3)
- **Label Status:** {'Present & Permanently Affixed' if intake.has_identification_label else 'Missing'}
- **Exact Text:** *"{intake.identification_label_text}"*

### 5.3 Warning Logotype Label (21 CFR 1040.10(g))
- **Label Status:** {'Present & Permanently Affixed' if intake.has_warning_logotype else 'Missing'}
- **Class & Warning Level:** {intake.laser_class}
- **Exact Text:** *"{intake.warning_logotype_text}"*

### 5.4 Aperture & Interlock Defeat Labels
- **Aperture Warning Label (1040.10(g)(4)):** *"{intake.aperture_label_text}"*
- **Interlock Defeat Label (1040.10(g)(6)):** *"{intake.interlock_defeat_label_text}"*

---

## Part 6: Quality Control, In-Line Testing, and Calibration (21 CFR 1002.30)

1. **Incoming Component Inspection:**
   - {intake.incoming_inspection_protocol}
2. **In-Line 100% Production Testing:**
   - {intake.inline_production_test_protocol}
3. **Measurement System Calibration & Traceability:**
   - Test equipment NIST-traceable: {'Yes' if intake.test_equipment_calibrated else 'No'}
   - Standard: {intake.calibration_standard}
4. **Life & Environmental Durability Records:**
   - Quality records maintained on file for 5 years pursuant to 21 CFR 1002.30(a).

---

## Part 7: User Safety Information & Servicing Instructions (21 CFR 1040.10(h))

- **User Operator Manual:** Includes mandatory radiation safety instructions, beam path diagram, eye protection ratings, and avoidance of specular reflections.
- **Servicing & Maintenance Guide:** {intake.servicing_safety_details}

---

## Part 8: Submitter Certification and Legal Attestation

> "I certify that all information contained herein is true and correct to the best of my knowledge and belief, and that the product(s) described herein will comply with all applicable radiation safety performance standards prescribed in Title 21 of the Code of Federal Regulations, Chapter I, Subchapter J - Radiological Health."

- **Authorized Certifier:** {certifier}
- **Title:** {intake.certifier_title}
- **Representing:** {intake.manufacturer_name}
- **Date Signed:** {intake.submission_date}
- **Accession Number Assigned by FDA:** _______________________ (Assigned upon CDRH review)
"""
    return md

def generate_pdf_report(intake: LaserProductIntake, output_pdf_path: Path):
    """Generate a publication-grade PDF Radiation Safety Product Report using ReportLab."""
    output_pdf_path.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(output_pdf_path),
        pagesize=letter,
        leftMargin=40,
        rightMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    styles = getSampleStyleSheet()
    normal = styles["Normal"]

    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=15,
        leading=18,
        textColor=colors.HexColor("#0B2545"),
        alignment=TA_CENTER
    )
    subtitle_style = ParagraphStyle(
        "ReportSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#134074"),
        alignment=TA_CENTER
    )
    h2_style = ParagraphStyle(
        "SectionH2",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=14,
        textColor=colors.HexColor("#0B2545"),
        spaceBefore=10,
        spaceAfter=4
    )
    body_style = ParagraphStyle(
        "BodyDark",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=11.5,
        textColor=colors.HexColor("#1D2D44")
    )
    table_cell = ParagraphStyle(
        "TableCell",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=7.5,
        leading=9.5,
        textColor=colors.HexColor("#1D2D44")
    )
    table_cell_bold = ParagraphStyle(
        "TableCellBold",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=7.5,
        leading=9.5,
        textColor=colors.HexColor("#0B2545")
    )

    story = []

    # Title & Header
    story.append(Paragraph(f"RADIATION SAFETY PRODUCT REPORT OF {intake.product_name.upper()}", title_style))
    story.append(Spacer(1, 3))
    story.append(Paragraph("PREPARED PURSUANT TO FORM FDA 3632 GUIDE & 21 CFR 1002.10 (EPRC)", subtitle_style))
    story.append(Paragraph("CDRH Electronic Product Radiation Control • U.S. Food and Drug Administration", subtitle_style))
    story.append(Spacer(1, 8))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#0B2545"), spaceAfter=10))

    # Meta Overview Box
    meta_data = [
        [Paragraph("<b>Manufacturer:</b>", table_cell), Paragraph(intake.manufacturer_name, table_cell),
         Paragraph("<b>Date of Report:</b>", table_cell), Paragraph(intake.submission_date, table_cell)],
        [Paragraph("<b>Model Family:</b>", table_cell), Paragraph(", ".join(intake.model_family), table_cell),
         Paragraph("<b>Laser Class:</b>", table_cell), Paragraph(f"<b>{intake.laser_class}</b>", table_cell_bold)],
        [Paragraph("<b>Wavelength(s):</b>", table_cell), Paragraph(", ".join(intake.emission_wavelengths), table_cell),
         Paragraph("<b>Max Radiant Power:</b>", table_cell), Paragraph(intake.max_output_power, table_cell)],
        [Paragraph("<b>US Agent:</b>", table_cell), Paragraph(intake.us_agent_name or "N/A (Domestic)", table_cell),
         Paragraph("<b>Submission Channel:</b>", table_cell), Paragraph("RadHealthCustomerService@fda.hhs.gov", table_cell)]
    ]
    meta_table = Table(meta_data, colWidths=[80, 185, 100, 165])
    meta_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#EEF4F8")),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#8DA9C4")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D0DBE5")),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 10))

    # Part 1: Identification
    story.append(Paragraph("PART 1: IDENTIFICATION OF MANUFACTURER & US DESIGNATED AGENT", h2_style))
    p1_data = [
        [Paragraph("Manufacturer Legal Entity", table_cell_bold), Paragraph(intake.manufacturer_name, table_cell)],
        [Paragraph("Operating Address", table_cell_bold), Paragraph(f"{intake.manufacturer_address}, {intake.country_of_origin}", table_cell)],
        [Paragraph("Regulatory Contact", table_cell_bold), Paragraph(f"{intake.contact_person} ({intake.certifier_title}) | {intake.contact_email} | {intake.contact_phone}", table_cell)],
        [Paragraph("US Agent for Service (21 CFR 1005.25)", table_cell_bold), Paragraph(f"{intake.us_agent_name or 'N/A'}; {intake.us_agent_address}; {intake.us_agent_email}", table_cell)]
    ]
    t1 = Table(p1_data, colWidths=[160, 370])
    t1.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#F8FAFC")),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    story.append(t1)
    story.append(Spacer(1, 8))

    # Part 2: Laser Characteristics
    story.append(Paragraph("PART 2: RADIATION EMISSION & CLASSIFICATION CHARACTERISTICS (21 CFR 1040.10)", h2_style))
    p2_data = [
        [Paragraph("Active Medium / Architecture", table_cell_bold), Paragraph(intake.active_medium, table_cell),
         Paragraph("Operational Mode", table_cell_bold), Paragraph(intake.operational_mode, table_cell)],
        [Paragraph("Emission Wavelength(s)", table_cell_bold), Paragraph(", ".join(intake.emission_wavelengths), table_cell),
         Paragraph("Max Output Power", table_cell_bold), Paragraph(intake.max_output_power, table_cell)],
        [Paragraph("Beam Divergence", table_cell_bold), Paragraph(intake.beam_divergence_mrad, table_cell),
         Paragraph("Beam Aperture Diameter", table_cell_bold), Paragraph(intake.beam_diameter_aperture_mm, table_cell)],
        [Paragraph("Conformance Standard", table_cell_bold), Paragraph(intake.conformance_standard, table_cell),
         Paragraph("Laser Class", table_cell_bold), Paragraph(f"<b>{intake.laser_class}</b>", table_cell_bold)]
    ]
    t2 = Table(p2_data, colWidths=[130, 135, 130, 135])
    t2.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#F8FAFC")),
        ("BACKGROUND", (2, 0), (2, -1), colors.HexColor("#F8FAFC")),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    story.append(t2)
    story.append(Spacer(1, 8))

    # Part 3: Engineering Safety Features Table
    story.append(Paragraph("PART 3: MANDATORY ENGINEERING SAFETY FEATURES (21 CFR 1040.10(f))", h2_style))
    p3_headers = [Paragraph("<b>Feature</b>", table_cell_bold), Paragraph("<b>21 CFR Clause</b>", table_cell_bold),
                  Paragraph("<b>Status</b>", table_cell_bold), Paragraph("<b>Engineering Implementation Description</b>", table_cell_bold)]
    p3_rows = [
        p3_headers,
        [Paragraph("Protective Housing", table_cell_bold), Paragraph("1040.10(f)(1)", table_cell),
         Paragraph("COMPLIANT", table_cell_bold), Paragraph(intake.protective_housing_details, table_cell)],
        [Paragraph("Safety Interlocks", table_cell_bold), Paragraph("1040.10(f)(2)", table_cell),
         Paragraph("COMPLIANT" if intake.has_safety_interlock else "N/A", table_cell), Paragraph(intake.safety_interlock_details, table_cell)],
        [Paragraph("Remote Interlock Connector", table_cell_bold), Paragraph("1040.10(f)(3)", table_cell),
         Paragraph("COMPLIANT" if intake.has_remote_interlock_connector else "N/A", table_cell), Paragraph(intake.remote_interlock_details, table_cell)],
        [Paragraph("Key Control", table_cell_bold), Paragraph("1040.10(f)(4)", table_cell),
         Paragraph("COMPLIANT" if intake.has_key_control else "N/A", table_cell), Paragraph(intake.key_control_details, table_cell)],
        [Paragraph("Beam Attenuator / Shutter", table_cell_bold), Paragraph("1040.10(f)(6)", table_cell),
         Paragraph("COMPLIANT" if intake.has_beam_attenuator else "N/A", table_cell), Paragraph(intake.beam_attenuator_details, table_cell)],
        [Paragraph("Emission Indicator", table_cell_bold), Paragraph("1040.10(f)(5)", table_cell),
         Paragraph("COMPLIANT" if intake.has_emission_indicator else "N/A", table_cell), Paragraph(intake.emission_indicator_details, table_cell)],
        [Paragraph("Viewing Optics / Window", table_cell_bold), Paragraph("1040.10(f)(8)", table_cell),
         Paragraph("COMPLIANT" if intake.has_viewing_optics_filter else "N/A", table_cell), Paragraph(intake.viewing_optics_details, table_cell)],
    ]
    t3 = Table(p3_rows, colWidths=[120, 70, 70, 270])
    t3.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E2E8F0")),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ("TOPPADDING", (0, 0), (-1, -1), 2.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
    ]))
    story.append(t3)
    story.append(Spacer(1, 8))

    # Part 4: Labeling Specifications
    story.append(Paragraph("PART 4: REQUIRED STATUTORY LABELING & MARKINGS (21 CFR 1010.2, 1010.3, 1040.10(g))", h2_style))
    p4_data = [
        [Paragraph("Certification Label (21 CFR 1010.2)", table_cell_bold), Paragraph(intake.certification_label_text, table_cell)],
        [Paragraph("Identification Label (21 CFR 1010.3)", table_cell_bold), Paragraph(intake.identification_label_text, table_cell)],
        [Paragraph("Warning Logotype Label (1040.10(g))", table_cell_bold), Paragraph(intake.warning_logotype_text, table_cell)],
        [Paragraph("Aperture Label (1040.10(g)(4))", table_cell_bold), Paragraph(intake.aperture_label_text, table_cell)],
        [Paragraph("Interlock Defeat Label (1040.10(g)(6))", table_cell_bold), Paragraph(intake.interlock_defeat_label_text, table_cell)]
    ]
    t4 = Table(p4_data, colWidths=[160, 370])
    t4.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#F8FAFC")),
        ("TOPPADDING", (0, 0), (-1, -1), 2.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
    ]))
    story.append(t4)
    story.append(Spacer(1, 8))

    # Part 5: Quality Control & Testing
    story.append(Paragraph("PART 5: QUALITY CONTROL, IN-LINE TESTING & CALIBRATION (21 CFR 1002.30)", h2_style))
    qc_text = f"<b>Incoming Verification:</b> {intake.incoming_inspection_protocol}<br/>" \
              f"<b>Production Testing:</b> {intake.inline_production_test_protocol}<br/>" \
              f"<b>Measurement Calibration:</b> {intake.calibration_standard} (NIST-traceable: {'Yes' if intake.test_equipment_calibrated else 'No'})"
    story.append(Paragraph(qc_text, body_style))
    story.append(Spacer(1, 10))

    # Part 6: Legal Attestation & Signature
    story.append(Paragraph("PART 6: LEGAL CERTIFICATION AND ATTESTATION", h2_style))
    attestation = "I certify that all information contained herein is true and correct to the best of my knowledge and belief, and that the product(s) described herein will comply with all applicable radiation safety performance standards prescribed in Title 21 of the Code of Federal Regulations, Chapter I, Subchapter J - Radiological Health."
    story.append(Paragraph(attestation, body_style))
    story.append(Spacer(1, 12))

    certifier = intake.certifier_name or intake.contact_person
    sig_data = [
        [Paragraph(f"<b>Authorized Representative:</b> {certifier}", table_cell),
         Paragraph(f"<b>Date:</b> {intake.submission_date}", table_cell)],
        [Paragraph(f"<b>Title:</b> {intake.certifier_title}", table_cell),
         Paragraph("<b>FDA Accession No.:</b> _____________________", table_cell)]
    ]
    sig_table = Table(sig_data, colWidths=[270, 260])
    sig_table.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(sig_table)

    doc.build(story)
    logger.info(f"Generated PDF report: {output_pdf_path}")

def create_sample_intake() -> LaserProductIntake:
    """Return a fully configured sample intake for testing and demonstration."""
    return LaserProductIntake(
        product_name="Ortur Laser Master Pro 3 Desktop Engraver",
        model_family=["OLM3-20W", "OLM3-10W", "OLM3-LE-5W"],
        brand_name="ORTUR",
        manufacturer_name="Dongguan Ortur Intelligent Technologies Co., Ltd.",
        manufacturer_address="Building 1, No. 6 Tianhao Road, Dongcheng District, Dongguan, Guangdong, China",
        country_of_origin="China",
        contact_person="Justin Zhang",
        contact_email="regulatory@ortur.cn",
        contact_phone="+86-769-82688888",
        us_agent_name="EPRC US Agent Services LLC",
        us_agent_address="1209 Orange Street, Wilmington, DE 19801",
        us_agent_phone="+1 (302) 555-0199",
        us_agent_email="compliance@eprcagent.com",
        laser_class="Class IV",
        conformance_standard="Laser Notice 56 / IEC 60825-1:2014 Ed. 3 & 21 CFR 1040.10",
        active_medium="Semiconductor InGaN Laser Diode Array",
        operational_mode="Continuous Wave (CW)",
        emission_wavelengths=["450 nm"],
        max_output_power="20.0 W radiant optical flux",
        beam_divergence_mrad="1.2 mrad",
        beam_diameter_aperture_mm="5.5 mm",
        has_protective_housing=True,
        protective_housing_details="Enclosed CNC chassis with optical filtration hood reducing accessible radiation outside working area.",
        has_safety_interlock=True,
        safety_interlock_details="Magnetic safety interlock switches wired to microcontroller cut off diode drive current within 15 ms upon enclosure lift.",
        has_remote_interlock_connector=True,
        remote_interlock_details="Standard 2-pole phoenix connector for external emergency stop button or room perimeter switches.",
        has_key_control=True,
        key_control_details="Physical rotary cylinder key control located on chassis front fascia; key captive in ENABLE state.",
        has_beam_attenuator=True,
        beam_attenuator_details="Spring-loaded solenoid mechanical shutter closes beam aperture upon power fault or command.",
        has_emission_indicator=True,
        emission_indicator_details="Dual optical amber indicators and audible chime providing 5-second advance warning before laser firing.",
        has_viewing_optics_filter=True,
        viewing_optics_details="Enclosure observation pane rated OD 6+ at 400-500nm laser wavelength.",
        has_scan_failure_safeguard=False,
        certifier_name="Justin Zhang",
        certifier_title="Director of Engineering & Regulatory Compliance",
        submission_date="2026-11-02"
    )

def main():
    parser = argparse.ArgumentParser(description="Form FDA 3632 Radiation Safety Product Report Generator.")
    parser.add_argument("--sample", action="store_true", help="Generate sample report for testing.")
    parser.add_argument("--input", type=str, help="Path to intake JSON file.")
    parser.add_argument("--output-md", type=str, help="Output path for Markdown report.")
    parser.add_argument("--output-pdf", type=str, help="Output path for PDF report.")
    parser.add_argument("--validate-only", action="store_true", help="Only validate compliance without saving.")
    args = parser.parse_args()

    if args.input:
        with open(args.input, "r", encoding="utf-8") as f:
            data = json.load(f)
        intake = LaserProductIntake.from_dict(data)
    else:
        intake = create_sample_intake()

    # Validation
    val_result = validate_intake_compliance(intake)
    print(f"Compliance validation status: {'COMPLIANT' if val_result['compliant'] else 'NON-COMPLIANT'}")
    if val_result["issues"]:
        print("Issues found:")
        for issue in val_result["issues"]:
            print(f"  - [CRITICAL] {issue}")
    if val_result["warnings"]:
        print("Warnings:")
        for w in val_result["warnings"]:
            print(f"  - [WARNING] {w}")

    if args.validate_only:
        return

    # Output defaults
    default_out_dir = Path(__file__).resolve().parent / "data"
    default_out_dir.mkdir(parents=True, exist_ok=True)
    slug = intake.product_name.lower().replace(" ", "_")[:30]
    out_md = Path(args.output_md) if args.output_md else default_out_dir / f"FDA_3632_Product_Report_{slug}.md"
    out_pdf = Path(args.output_pdf) if args.output_pdf else default_out_dir / f"FDA_3632_Product_Report_{slug}.pdf"

    md_content = generate_markdown_report(intake)
    out_md.write_text(md_content, encoding="utf-8")
    print(f"Saved Markdown report to: {out_md}")

    generate_pdf_report(intake, out_pdf)
    print(f"Saved PDF report to: {out_pdf}")

if __name__ == "__main__":
    main()
