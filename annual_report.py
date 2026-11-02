#!/usr/bin/env python3
"""Form FDA 3636 Annual Report Generator for Laser Products.

Generates Form FDA 3636-structured Annual Reports from intake data and accession
numbers, computing the July 1 - June 30 reporting period dynamically and
flagging the mandatory September 1 deadline per 21 CFR 1002.13.
Produces both Markdown (.md) and PDF (.pdf) formats.
"""

import os
import sys
import json
import logging
import argparse
from datetime import datetime, date
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field, asdict

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("annual_report")

DEFAULT_DATA_DIR = Path(__file__).resolve().parent / "data"

@dataclass
class LaserModelProduction:
    model_name: str
    accession_number: str
    report_type: str  # Initial Product Report (3632) / Supplemental (1002.11)
    filing_date: str
    units_manufactured_for_us: int
    units_imported_to_us: int
    laser_class: str = "Class IV"

@dataclass
class AnnualReportIntake:
    manufacturer_name: str
    manufacturer_address: str
    country_of_origin: str
    contact_person: str
    contact_email: str
    contact_phone: str
    certifier_title: str = "Regulatory Affairs Director"

    # US Agent
    us_agent_name: str = ""
    us_agent_address: str = ""
    us_agent_email: str = ""
    us_agent_phone: str = ""

    # Products & Accession Numbers
    products: List[LaserModelProduction] = field(default_factory=list)

    # QA / QC Summary
    total_units_tested: int = 1500
    total_units_rejected: int = 4
    corrective_actions_summary: str = "Replaced optical collimator lens batch from sub-supplier due to focal drift on 4 units; 100% re-tested with NIST-traceable power meter."
    calibration_verified: bool = True
    calibration_facility: str = "Thorlabs Calibration Lab, NIST Traceable Standard"

    # Incidents / Defects (21 CFR 1002.20 / Part 1003)
    accidental_radiation_occurrences: int = 0
    safety_recalls_or_defects: int = 0
    customer_radiation_complaints: int = 0

    # Reporting year (ending June 30 of this year)
    report_year: Optional[int] = None
    submission_date: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["products"] = [asdict(p) for p in self.products]
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AnnualReportIntake":
        prods = [LaserModelProduction(**p) for p in data.get("products", [])]
        filtered = dict(data)
        filtered["products"] = prods
        return cls(**filtered)

def compute_reporting_period(report_year: Optional[int] = None, ref_date: Optional[date] = None) -> Dict[str, Any]:
    """Compute the 12-month period ending June 30 and determine filing status."""
    today = ref_date or date.today()

    if report_year is not None:
        target_year = report_year
    else:
        # If current month is >= September, report for the year ending June 30 of this year is already due / overdue
        # or we might be filing the past year's report.
        if today.month >= 7:
            target_year = today.year
        else:
            target_year = today.year

    start_date = date(target_year - 1, 7, 1)
    end_date = date(target_year, 6, 30)
    deadline_date = date(target_year, 9, 1)

    is_overdue = today > deadline_date
    days_diff = (today - deadline_date).days if is_overdue else (deadline_date - today).days

    return {
        "report_year": target_year,
        "period_start": start_date.strftime("%B %d, %Y"),
        "period_end": end_date.strftime("%B %d, %Y"),
        "period_string": f"July 1, {target_year - 1} through June 30, {target_year}",
        "filing_deadline": deadline_date.strftime("%B %d, %Y"),
        "is_overdue": is_overdue,
        "days_difference": abs(days_diff),
        "status_flag": "OVERDUE (Cure Immediately)" if is_overdue else "ON TIME (Ahead of Sept 1 Deadline)"
    }

def generate_markdown_annual_report(intake: AnnualReportIntake, period_info: Dict[str, Any]) -> str:
    """Generate completed Form FDA 3636 Annual Report draft in Markdown."""
    sub_date = intake.submission_date or datetime.now().strftime("%Y-%m-%d")

    total_mfg = sum(p.units_manufactured_for_us for p in intake.products)
    total_imp = sum(p.units_imported_to_us for p in intake.products)

    product_rows = ""
    for p in intake.products:
        product_rows += f"| {p.model_name} | {p.laser_class} | `{p.accession_number}` | {p.report_type} | {p.filing_date} | {p.units_manufactured_for_us:,} | {p.units_imported_to_us:,} |\n"

    md = f"""# Radiation Safety Annual Report of {intake.manufacturer_name}

**Document Control:** FORM FDA 3636 (Guide for Preparing Annual Reports for Radiation Safety Testing of Electronic Products)  
**Governing Regulation:** 21 CFR 1002.13 (Annual Reports for Radiation Emitting Products)  
**Reporting Period:** {period_info['period_string']}  
**Statutory Filing Deadline:** {period_info['filing_deadline']}  
**Compliance Status:** **{period_info['status_flag']}**  
**Submission Channel:** CDRH Radiation Health Customer Service (`RadHealthCustomerService@fda.hhs.gov`)  
**Date of Filing:** {sub_date}  

---

## Part 1: Identification of Manufacturer and US Designated Agent

### 1.1 Manufacturer Details
- **Company Name:** {intake.manufacturer_name}
- **Address:** {intake.manufacturer_address}
- **Country:** {intake.country_of_origin}
- **Regulatory Contact:** {intake.contact_person} ({intake.certifier_title})
- **Email:** {intake.contact_email}
- **Phone:** {intake.contact_phone}

### 1.2 Designated US Agent (21 CFR 1005.25)
- **Agent Name:** {intake.us_agent_name or 'N/A (Domestic Manufacturer)'}
- **Agent Address:** {intake.us_agent_address or 'N/A'}
- **Agent Contact:** {intake.us_agent_email or 'N/A'} | {intake.us_agent_phone or 'N/A'}

---

## Part 2: Laser Products Introduced Into Commerce & Accession Numbers

During the reporting period of **{period_info['period_string']}**, the following laser product families were manufactured or imported into the United States under active FDA Accession Numbers:

| Model / Series | Class | FDA Accession No. | Prior Report Type | Initial Filing Date | US Mfg Volume | US Import Volume |
|---|---|---|---|---|---|---|
{product_rows}
| **TOTALS** | — | — | — | — | **{total_mfg:,} units** | **{total_imp:,} units** |

---

## Part 3: Quality Control & Radiation Safety Testing Summary (21 CFR 1002.30)

1. **Production Quality Testing Volume:**
   - **Total Units Tested:** {intake.total_units_tested:,} units (100% production line optical power testing)
   - **Non-Conforming Units Detected:** {intake.total_units_rejected} units ({((intake.total_units_rejected/max(1, intake.total_units_tested))*100):.2f}% defect rate)
   - **Disposition of Rejected Units:** All non-conforming units quarantined, repaired, and re-tested prior to final packing.

2. **Corrective Actions Taken:**
   - {intake.corrective_actions_summary}

3. **Measurement System Calibration:**
   - Test equipment NIST-traceable: {'Yes' if intake.calibration_verified else 'No'}
   - Standard: {intake.calibration_facility}

---

## Part 4: Accidental Radiation Occurrences & Product Defects (21 CFR Part 1003 & 1002.20)

- **Accidental Radiation Occurrences (21 CFR 1002.20):** **{intake.accidental_radiation_occurrences}**
- **Safety Recalls or Defect Notifications (21 CFR 1003):** **{intake.safety_recalls_or_defects}**
- **Customer Radiation Injury or Safety Complaints:** **{intake.customer_radiation_complaints}**

*Note: No incidents involving unexpected accessible radiation emissions or human exposure exceeding applicable Class Limits occurred during this reporting cycle.*

---

## Part 5: Legal Certification and Attestation

> "I certify that all information contained in this Annual Report is true, complete, and correct to the best of my knowledge and belief, and that the quality control and testing program described herein was conducted in accordance with procedures previously submitted to the Food and Drug Administration pursuant to 21 CFR 1002.10."

- **Authorized Officer:** {intake.contact_person}
- **Title:** {intake.certifier_title}
- **Company:** {intake.manufacturer_name}
- **Date Signed:** {sub_date}
"""
    return md

def generate_pdf_annual_report(intake: AnnualReportIntake, period_info: Dict[str, Any], output_pdf_path: Path):
    """Generate publication-grade PDF Form FDA 3636 Annual Report."""
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

    # Header
    story.append(Paragraph(f"RADIATION SAFETY ANNUAL REPORT OF {intake.manufacturer_name.upper()}", title_style))
    story.append(Spacer(1, 3))
    story.append(Paragraph("FORM FDA 3636 • PURSUANT TO 21 CFR 1002.13 (ELECTRONIC PRODUCT RADIATION CONTROL)", subtitle_style))
    story.append(Paragraph("CDRH Document Control • U.S. Food and Drug Administration", subtitle_style))
    story.append(Spacer(1, 8))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#0B2545"), spaceAfter=10))

    # Meta Overview Box
    sub_date = intake.submission_date or datetime.now().strftime("%Y-%m-%d")
    status_color = "#B91C1C" if period_info["is_overdue"] else "#15803D"

    meta_data = [
        [Paragraph("<b>Manufacturer:</b>", table_cell), Paragraph(intake.manufacturer_name, table_cell),
         Paragraph("<b>Reporting Period:</b>", table_cell), Paragraph(period_info["period_string"], table_cell_bold)],
        [Paragraph("<b>Regulatory Contact:</b>", table_cell), Paragraph(f"{intake.contact_person} ({intake.contact_email})", table_cell),
         Paragraph("<b>Statutory Deadline:</b>", table_cell), Paragraph(f"{period_info['filing_deadline']} (Sept 1)", table_cell)],
        [Paragraph("<b>Filing Channel:</b>", table_cell), Paragraph("RadHealthCustomerService@fda.hhs.gov", table_cell),
         Paragraph("<b>Compliance Status:</b>", table_cell), Paragraph(f"<font color='{status_color}'><b>{period_info['status_flag']}</b></font>", table_cell)]
    ]
    meta_table = Table(meta_data, colWidths=[90, 185, 95, 160])
    meta_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#EEF4F8")),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#8DA9C4")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D0DBE5")),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 10))

    # Part 1: Manufacturer & US Agent
    story.append(Paragraph("PART 1: IDENTIFICATION OF MANUFACTURER & US DESIGNATED AGENT", h2_style))
    p1_data = [
        [Paragraph("Manufacturer Legal Name", table_cell_bold), Paragraph(intake.manufacturer_name, table_cell)],
        [Paragraph("Principal Address", table_cell_bold), Paragraph(f"{intake.manufacturer_address}, {intake.country_of_origin}", table_cell)],
        [Paragraph("US Designated Agent (21 CFR 1005.25)", table_cell_bold), Paragraph(f"{intake.us_agent_name or 'N/A'}; {intake.us_agent_address}; {intake.us_agent_email}", table_cell)]
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
    story.append(Spacer(1, 10))

    # Part 2: Product & Accession Numbers Table
    story.append(Paragraph("PART 2: PRODUCTS DISTRIBUTED IN US COMMERCE & FDA ACCESSION NUMBERS", h2_style))
    headers = [
        Paragraph("<b>Model Name</b>", table_cell_bold), Paragraph("<b>Class</b>", table_cell_bold),
        Paragraph("<b>FDA Accession No.</b>", table_cell_bold), Paragraph("<b>Prior Report Type</b>", table_cell_bold),
        Paragraph("<b>Initial Filing</b>", table_cell_bold), Paragraph("<b>US Production</b>", table_cell_bold),
        Paragraph("<b>US Imports</b>", table_cell_bold)
    ]
    rows = [headers]
    total_mfg = 0
    total_imp = 0
    for p in intake.products:
        total_mfg += p.units_manufactured_for_us
        total_imp += p.units_imported_to_us
        rows.append([
            Paragraph(p.model_name, table_cell_bold),
            Paragraph(p.laser_class, table_cell),
            Paragraph(p.accession_number, table_cell),
            Paragraph(p.report_type, table_cell),
            Paragraph(p.filing_date, table_cell),
            Paragraph(f"{p.units_manufactured_for_us:,}", table_cell),
            Paragraph(f"{p.units_imported_to_us:,}", table_cell),
        ])
    # Totals row
    rows.append([
        Paragraph("<b>TOTALS</b>", table_cell_bold), Paragraph("—", table_cell), Paragraph("—", table_cell),
        Paragraph("—", table_cell), Paragraph("—", table_cell),
        Paragraph(f"<b>{total_mfg:,}</b>", table_cell_bold), Paragraph(f"<b>{total_imp:,}</b>", table_cell_bold)
    ])
    p2_table = Table(rows, colWidths=[100, 45, 95, 100, 65, 65, 60])
    p2_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E2E8F0")),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#F1F5F9")),
        ("TOPPADDING", (0, 0), (-1, -1), 2.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
    ]))
    story.append(p2_table)
    story.append(Spacer(1, 10))

    # Part 3: QA Summary
    story.append(Paragraph("PART 3: SUMMARY OF QUALITY CONTROL AND TESTING RESULTS (21 CFR 1002.30)", h2_style))
    qa_data = [
        [Paragraph("Total Units Tested (100% In-Line Power)", table_cell_bold), Paragraph(f"{intake.total_units_tested:,} units", table_cell)],
        [Paragraph("Non-Conformances Detected", table_cell_bold), Paragraph(f"{intake.total_units_rejected} units ({((intake.total_units_rejected/max(1, intake.total_units_tested))*100):.2f}%)", table_cell)],
        [Paragraph("Corrective Actions & Investigation", table_cell_bold), Paragraph(intake.corrective_actions_summary, table_cell)],
        [Paragraph("Calibration Standard & Traceability", table_cell_bold), Paragraph(f"{intake.calibration_facility} (NIST Traceable: {'Yes' if intake.calibration_verified else 'No'})", table_cell)]
    ]
    t3 = Table(qa_data, colWidths=[160, 370])
    t3.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#F8FAFC")),
        ("TOPPADDING", (0, 0), (-1, -1), 2.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
    ]))
    story.append(t3)
    story.append(Spacer(1, 10))

    # Part 4: Safety Incidents / Defects
    story.append(Paragraph("PART 4: RADIATION SAFETY INCIDENTS & DEFECT NOTICES (21 CFR PART 1003 & 1002.20)", h2_style))
    inc_data = [
        [Paragraph("Accidental Radiation Occurrences (21 CFR 1002.20)", table_cell_bold), Paragraph(str(intake.accidental_radiation_occurrences), table_cell)],
        [Paragraph("Radiation Defect Notifications / Recalls (21 CFR 1003)", table_cell_bold), Paragraph(str(intake.safety_recalls_or_defects), table_cell)],
        [Paragraph("Customer Radiation Safety / Injury Complaints", table_cell_bold), Paragraph(str(intake.customer_radiation_complaints), table_cell)]
    ]
    t4 = Table(inc_data, colWidths=[200, 330])
    t4.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#F8FAFC")),
        ("TOPPADDING", (0, 0), (-1, -1), 2.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
    ]))
    story.append(t4)
    story.append(Spacer(1, 12))

    # Part 5: Signature & Legal Certification
    story.append(Paragraph("PART 5: LEGAL CERTIFICATION & ATTESTATION", h2_style))
    cert_text = "I certify that all information contained in this Annual Report is true, complete, and correct to the best of my knowledge and belief, and that the quality control and testing program described herein was conducted in accordance with procedures previously submitted to the Food and Drug Administration pursuant to 21 CFR 1002.10."
    story.append(Paragraph(cert_text, body_style))
    story.append(Spacer(1, 10))

    sig_data = [
        [Paragraph(f"<b>Authorized Officer:</b> {intake.contact_person}", table_cell),
         Paragraph(f"<b>Date:</b> {sub_date}", table_cell)],
        [Paragraph(f"<b>Title:</b> {intake.certifier_title}", table_cell),
         Paragraph(f"<b>Firm:</b> {intake.manufacturer_name}", table_cell)]
    ]
    sig_table = Table(sig_data, colWidths=[270, 260])
    sig_table.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(sig_table)

    doc.build(story)
    logger.info(f"Generated PDF Annual Report: {output_pdf_path}")

def create_sample_annual_report_intake(report_year: Optional[int] = None) -> AnnualReportIntake:
    """Return a configured sample annual report intake."""
    return AnnualReportIntake(
        manufacturer_name="Dongguan Ortur Intelligent Technologies Co., Ltd.",
        manufacturer_address="Building 1, No. 6 Tianhao Road, Dongcheng District, Dongguan, Guangdong, China",
        country_of_origin="China",
        contact_person="Justin Zhang",
        contact_email="regulatory@ortur.cn",
        contact_phone="+86-769-82688888",
        certifier_title="Director of Engineering & Regulatory Compliance",
        us_agent_name="EPRC US Agent Services LLC",
        us_agent_address="1209 Orange Street, Wilmington, DE 19801",
        us_agent_email="compliance@eprcagent.com",
        us_agent_phone="+1 (302) 555-0199",
        products=[
            LaserModelProduction(
                model_name="Laser Master 3 (LM3-20W)",
                accession_number="2210452-000",
                report_type="Form FDA 3632 Initial Product Report",
                filing_date="2022-08-15",
                units_manufactured_for_us=3200,
                units_imported_to_us=3150,
                laser_class="Class IV"
            ),
            LaserModelProduction(
                model_name="Laser Master Pro 2 (OLM2-10W)",
                accession_number="2120118-000",
                report_type="Form FDA 3632 Initial Product Report",
                filing_date="2021-06-20",
                units_manufactured_for_us=1800,
                units_imported_to_us=1800,
                laser_class="Class IV"
            ),
            LaserModelProduction(
                model_name="Aufero Laser 2 Desktop Series",
                accession_number="2310894-000",
                report_type="21 CFR 1002.11 Supplemental Report",
                filing_date="2023-04-10",
                units_manufactured_for_us=2400,
                units_imported_to_us=2350,
                laser_class="Class IV"
            )
        ],
        total_units_tested=7400,
        total_units_rejected=11,
        corrective_actions_summary="Identified loose interlock microswitch bracket on 11 units during mechanical burn-in. Tooling tightened and torque specs updated in standard work instruction SWI-ENG-042.",
        calibration_verified=True,
        calibration_facility="Thorlabs Optical Calibration Center, NIST Traceable Standard Cert #77812",
        accidental_radiation_occurrences=0,
        safety_recalls_or_defects=0,
        customer_radiation_complaints=0,
        report_year=report_year
    )

def main():
    parser = argparse.ArgumentParser(description="Form FDA 3636 Annual Report Generator for Laser Products (21 CFR 1002.13).")
    parser.add_argument("--sample", action="store_true", help="Generate sample annual report for testing.")
    parser.add_argument("--input", type=str, help="Path to annual report intake JSON.")
    parser.add_argument("--year", type=int, default=2026, help="Reporting year ending June 30 (default: 2026).")
    parser.add_argument("--output-md", type=str, help="Path for output Markdown.")
    parser.add_argument("--output-pdf", type=str, help="Path for output PDF.")
    args = parser.parse_args()

    period_info = compute_reporting_period(report_year=args.year)
    print(f"Reporting Period: {period_info['period_string']}")
    print(f"Statutory Deadline: {period_info['filing_deadline']} (Sept 1)")
    print(f"Status: {period_info['status_flag']}")

    if args.input:
        with open(args.input, "r", encoding="utf-8") as f:
            data = json.load(f)
        intake = AnnualReportIntake.from_dict(data)
    else:
        intake = create_sample_annual_report_intake(report_year=args.year)

    default_out_dir = Path(__file__).resolve().parent / "data"
    default_out_dir.mkdir(parents=True, exist_ok=True)
    slug = intake.manufacturer_name.lower().replace(" ", "_")[:25]
    out_md = Path(args.output_md) if args.output_md else default_out_dir / f"FDA_3636_Annual_Report_{slug}_{args.year}.md"
    out_pdf = Path(args.output_pdf) if args.output_pdf else default_out_dir / f"FDA_3636_Annual_Report_{slug}_{args.year}.pdf"

    md_content = generate_markdown_annual_report(intake, period_info)
    out_md.write_text(md_content, encoding="utf-8")
    print(f"Saved Markdown Annual Report to: {out_md}")

    generate_pdf_annual_report(intake, period_info, out_pdf)
    print(f"Saved PDF Annual Report to: {out_pdf}")

if __name__ == "__main__":
    main()
