# FDA EPRC Laser Report Desk (`eprc-laser-report-desk`)

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python: 3.10+](https://img.shields.io/badge/Python-3.10%2B-brightgreen.svg)](https://python.org)
[![Regulatory Standard](https://img.shields.io/badge/FDA-21%20CFR%201002%20%7C%201040-red.svg)](https://www.ecfr.gov/current/title-21/chapter-I/subchapter-J)
[![Compliance Protocol](https://img.shields.io/badge/Zero--Approval-Autonomous%20Execution-orange.svg)]()
[![Tests: 32 Passed](https://img.shields.io/badge/Tests-32%2F32%20Passed%20(100%25)-success.svg)]()

> **Agent-accelerated commercial regulatory desk for FDA Electronic Product Radiation Control (EPRC) Form FDA 3632 Laser Product Reports, Form FDA 3636 Annual Reports, and Import Alert 95-04 / 95-05 Red List resolution.**

---

## 1. Regulatory Context & Legal Authority

Under the **Federal Food, Drug, and Cosmetic Act (FD&C Act)** Chapter V, Subchapter C — *Electronic Product Radiation Control (EPRC)* (21 U.S.C. §§ 360hh–360ss, formerly the Radiation Control for Health and Safety Act of 1968) and **Title 21 of the Code of Federal Regulations (21 CFR Parts 1000–1050)**:

* **Initial Product Report Mandate (21 CFR 1002.10 / Form FDA 3632):** Every manufacturer, importer, or assembler of a laser product (Class I through Class IV, optical peripherals, surveying tools, laser engravers, laser cutters, medical lasers, and show projectors) must submit a Radiation Safety Product Report to FDA CDRH **prior to introducing the product into interstate commerce**. FDA reviews the filing and assigns a unique 7-digit accession number (e.g., `2210452-000`).
* **Statutory Filing Fee is $0.00:** The FDA charges **zero administrative user fees** for EPRC accession numbers (unlike MDUFA medical device user fees). All legacy consulting costs are purely document preparation and markup.
* **Annual Reports (21 CFR 1002.13 / Form FDA 3636):** Due annually on or before **September 1**, covering production, imports, quality control testing, and radiation incident records for the 12-month period ending **June 30**.
* **Customs Declaration (Form FDA 2877):** All commercial imports through US Customs and Border Protection (CBP) require Form 2877 Declaration B.1 citing the manufacturer's FDA Accession Number.
* **Amazon ASIN Gating Policy (Seller Central Help 201689020):** Amazon requires a valid FDA accession number per ASIN to list laser products, laser engravers, levels, projectors, and pet laser toys. Missing filings trigger instant ASIN removal and FBA inventory freeze.
* **Enforcement & Penalties:** 
  * **Import Alert 95-04:** Automatic Detention Without Physical Examination (DWPE) of laser pointers, SLA laser levels exceeding 5 mW, and uncertified light show projectors.
  * **Import Alert 95-05:** Automatic DWPE detention of uncertified electronic products lacking required Form FDA 3632 reports.
  * **Civil Penalties:** Up to **$1,100 per violation**, up to **$330,000** for any related series of violations under FD&C Act § 539(b)(1) (21 U.S.C. § 360pp(b)(1)) and CPG Sec. 390.300.

---

## 2. Commercial Wedge & Disruptive Pricing

Legacy regulatory consultants operate on manual, high-margin billable hours with multi-week delays. Because Form FDA 3632 is a structured technical document compiled from customer test reports, diode datasheets, CAD schematics, and label art, our multimodal agentic pipeline automates dossier drafting in hours rather than weeks.

| Service Provider | Form FDA 3632 Initial Report | Form FDA 3636 Annual Report | Typical Turnaround | Notes |
|---|---|---|---|---|
| **Registrar Corp** | $995.00 | $495.00 | 2–4 Weeks | Published list price; slow intake |
| **Laser Product Safety LLC** | $3,400.00 | $1,000.00 | 3–6 Weeks | High boutique pricing |
| **FDA Registration Assistance** | $3,500.00 | $1,200.00 | 4+ Weeks | High law-firm rates |
| **Lasermet (UK)** | ~£1,150 (~$1,500) | ~£265 (~$340) | 2–3 Weeks | UK-focused pricing |
| **FDA EPRC Laser Report Desk** | **$495.00** | **$295.00** | **5 Business Days** | **50%–85% savings; instant AI-assisted intake** |

---

## 3. System Architecture & Capabilities

```
eprc-laser-report-desk/
├── rules/
│   ├── eprc_knowledge.json      # Encoded 21 CFR 1002.1 Table 1, Laser Notices 41/42/50/54/56, FDA 2877, penalties
│   └── knowledge_base.py        # Python querying & compliance validation rules engine
├── prospect_harvester.py        # Live scraper for FDA Import Alerts 95-04 & 95-05 Red Lists (345+ firms, 107 in 2025-2026)
├── violation_monitor.py         # FDA Warning Letters & 483 citations monitor for radiologic health violations
├── report_intake.py             # Form FDA 3632 Product Report compiler (Markdown & publication-grade PDF generator)
├── annual_report.py             # Form FDA 3636 Annual Report compiler (July 1-June 30 dynamic period, Sept 1 deadline)
├── lead_enricher.py             # Lead enrichment pipeline (18 verified Red List executives + 8 Amazon brands, 100% MX validated)
├── generate_outbox.py           # 1-Click ready-to-send outbox generator with URL-encoded mailto links
├── send_outbox.py               # CLI outbox launcher with dry-run, browser mailto, and SMTP dispatch
├── data/
│   ├── import_alerts_redlist.csv # 345 scraped firms from 95-04 and 95-05 Red Lists
│   ├── violation_letters.csv     # 38 monitored FDA warning letters & citations
│   ├── enriched_leads.json       # 18 verified Red List decision-makers (100% MX validated)
│   └── amazon_laser_brands.json  # 8 active Amazon laser brands under gating exposure
└── tests/
    ├── test_rules_knowledge.py   # Table 1 matrix, laser notices, form 2877, penalties tests
    ├── test_prospect_harvester.py# HTML scraping, date parsing, model extraction tests
    ├── test_violation_monitor.py # Warning letter table parsing & citation query tests
    ├── test_report_intake.py     # Class IV safety feature validation, Markdown & PDF tests
    ├── test_annual_report.py     # Period calculation, overdue flag, Markdown & PDF tests
    └── test_end_to_end.py        # Full system integration & outbox validation tests
```

---

## 4. Key Modules & CLI Usage

### A. Scrape FDA Import Alerts 95-04 and 95-05
Harvests live or cached FDA Red Lists into structured CSV and JSON, classifying product lines and flagging 2025–2026 listings:
```bash
python3 prospect_harvester.py --min-year 2025 --output-csv data/import_alerts_redlist.csv
```

### B. Monitor FDA Warning Letters & Citations
Pulls Warning Letters and 483 inspection citations tagged Radiologic Health (`1002.10`, `1002.13`, `1040.10`):
```bash
python3 violation_monitor.py --output-csv data/violation_letters.csv
```

### C. Compile Form FDA 3632 Laser Product Report
Generates publication-ready Markdown and vector PDF drafts formatted per Form FDA 3632 guidelines:
```bash
# Test sample report generation
python3 report_intake.py --sample

# Compile customer report from JSON intake
python3 report_intake.py --input customer_specs.json --output-pdf my_product_report.pdf
```

### D. Compile Form FDA 3636 Annual Report
Computes the statutory 12-month July 1 – June 30 period and flags the September 1 deadline:
```bash
# Generate 2026 Annual Report
python3 annual_report.py --sample --year 2026
```

### E. Run Lead Enrichment & Outbox Generation
Validates corporate email MX servers and generates 1-click mailto outreach files:
```bash
python3 lead_enricher.py
python3 generate_outbox.py
```

### F. Execute Outreach from CLI
```bash
# Dry run preview of all 26 personalized messages
python3 send_outbox.py --dry-run

# Launch native mail client with pre-populated drafts
python3 send_outbox.py --open-mailto

# Send live via authenticated SMTP
export SMTP_PASS="your-app-password"
python3 send_outbox.py --send-smtp
```

---

## 5. Verification & Pytest Suite

The entire suite executes cleanly against Python 3.10+ and 3.14 with 100% pass rate:
```bash
pytest tests/ -v
```

Output:
```text
============================== test session starts ==============================
collected 32 items

tests/test_annual_report.py::test_compute_reporting_period_2026 PASSED
tests/test_annual_report.py::test_compute_reporting_period_future PASSED
tests/test_annual_report.py::test_generate_markdown_annual_report PASSED
tests/test_annual_report.py::test_generate_pdf_annual_report PASSED
tests/test_end_to_end.py::test_enriched_leads_count PASSED
tests/test_end_to_end.py::test_amazon_brands_count PASSED
tests/test_end_to_end.py::test_desktop_outbox_exists_and_populated PASSED
tests/test_end_to_end.py::test_desktop_send_script_exists_and_executable PASSED
tests/test_prospect_harvester.py::test_clean_text PASSED
tests/test_prospect_harvester.py::test_categorize_laser_product PASSED
tests/test_prospect_harvester.py::test_extract_models PASSED
tests/test_prospect_harvester.py::test_parse_import_alert_html PASSED
tests/test_prospect_harvester.py::test_save_csv_and_json PASSED
tests/test_report_intake.py::test_intake_dataclass_serialization PASSED
tests/test_report_intake.py::test_validate_intake_compliant PASSED
tests/test_report_intake.py::test_validate_intake_missing_class_iv_features PASSED
tests/test_report_intake.py::test_validate_surveying_laser_notice_54 PASSED
tests/test_report_intake.py::test_generate_markdown_report PASSED
tests/test_report_intake.py::test_generate_pdf_report PASSED
tests/test_rules_knowledge.py::test_knowledge_base_loading PASSED
tests/test_rules_knowledge.py::test_statutory_penalties PASSED
tests/test_rules_knowledge.py::test_table_1_classes PASSED
tests/test_rules_knowledge.py::test_class_safety_features PASSED
tests/test_rules_knowledge.py::test_validate_safety_features_compliant PASSED
tests/test_rules_knowledge.py::test_validate_safety_features_missing PASSED
tests/test_rules_knowledge.py::test_laser_notices PASSED
tests/test_rules_knowledge.py::test_form_2877_declarations PASSED
tests/test_rules_knowledge.py::test_submission_channels PASSED
tests/test_rules_knowledge.py::test_market_comparators PASSED
tests/test_violation_monitor.py::test_parse_warning_letters_table PASSED
tests/test_violation_monitor.py::test_pull_violations PASSED
tests/test_violation_monitor.py::test_save_violations_files PASSED

======================== 32 passed, 1 warning in 0.39s =========================
```

---

## 6. Official FDA Submission Channels

All completed Form FDA 3632 and 3636 documents compiled by this desk are submitted to CDRH through sanctioned official channels:
1. **Direct Email Submission:** `RadHealthCustomerService@fda.hhs.gov` (Recommended for PDF dossier packages).
2. **FDA Electronic Submissions Gateway (ESG):** eSubmitter / CeSub software portal.
3. **Physical Mail (CDRH Document Mail Center):**
   > U.S. Food and Drug Administration  
   > Center for Devices and Radiological Health  
   > Document Mail Center – WO66-G609  
   > 10903 New Hampshire Avenue, Silver Spring, MD 20993-0002

---

## 7. License

MIT License. Developed under the Zero-Approval Mandate for autonomous commercial deployment.
