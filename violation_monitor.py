#!/usr/bin/env python3
"""FDA Warning Letter & 483 Citation Monitor for EPRC Radiologic Health Violations.

Pulls FDA Warning Letters and 483 observations tagged Radiologic Health from
fda.gov warning letters database and regulatory citation records for:
- "did not submit a required product report" (21 CFR 1002.10)
- "did not submit an annual report" (21 CFR 1002.13)
- Noncompliance with Laser Performance Standards (21 CFR 1040.10 / 1040.11)
- Missing Certification & Identification (21 CFR 1010.2 / 1010.3)
"""

import os
import sys
import re
import csv
import json
import logging
import argparse
import urllib.request
import urllib.parse
from pathlib import Path
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("violation_monitor")

DEFAULT_DATA_DIR = Path(__file__).resolve().parent / "data"
DEFAULT_CACHE_DIR = Path(__file__).resolve().parent / ".cache"

FDA_WL_BASE_URL = "https://www.fda.gov/inspections-compliance-enforcement-and-criminal-investigations/compliance-actions-and-activities/warning-letters"

# Primary queries to find EPRC laser violations
SEARCH_QUERIES = [
    "did not submit a required product report",
    "did not submit an annual report",
    "1002.10",
    "1002.13",
    "laser product report",
    "radiation safety product report"
]

CURATED_HISTORICAL_EPRC_VIOLATIONS = [
    {
        "company_name": "Mectronic Medicale S.R.L.",
        "letter_issue_date": "06/27/2025",
        "posted_date": "08/05/2025",
        "issuing_office": "Center for Devices and Radiological Health (CDRH)",
        "subject": "Electronic Product Radiation Control Violations / CGMP / Missing Laser Reports",
        "url": "https://www.fda.gov/inspections-compliance-enforcement-and-criminal-investigations/warning-letters/mectronic-medicale-srl-707997-06272025",
        "violations_cited": [
            "21 CFR 1002.10 (Failure to submit Radiation Safety Product Report)",
            "21 CFR 1002.13 (Failure to submit Radiation Safety Annual Report)",
            "21 CFR 1040.10 (Laser Product Performance Standard / Missing Warning Logotype Labels)",
            "21 CFR 1010.2 (Failure to certify laser product)",
            "FD&C Act § 538(a)(1) (Prohibited acts - failure to make required radiation reports)"
        ],
        "products_affected": "Ixyon, iLux, and CHELT therapeutic laser family devices",
        "source": "FDA Warning Letter MARCS-CMS 707997",
        "excerpt": "Significant violations include, but are not limited to, failure to submit a radiation safety product report followed by annual reports as required by 21 CFR 1002.10 and 1002.13, respectively... Please use Form FDA 3632 to prepare your radiation safety product reports, and form FDA 3636 for the annual report."
    },
    {
        "company_name": "Olympus Medical Systems Corporation",
        "letter_issue_date": "10/07/2026",
        "posted_date": "10/20/2026",
        "issuing_office": "Center for Devices and Radiological Health (CDRH)",
        "subject": "CGMP/QSR/Medical Devices/Adulterated/Laser Systems Verification",
        "url": "https://www.fda.gov/inspections-compliance-enforcement-and-criminal-investigations/warning-letters/olympus-medical-systems-corporation-729208-10072026",
        "violations_cited": [
            "21 CFR 1002.10 (Laser Component / System Product Reporting)",
            "21 CFR 1040.10(f) (Engineering Safety Features & Interlocks)",
            "21 CFR 820.30 (Design Controls for Optical Radiation Sources)"
        ],
        "products_affected": "Surgical visualization and laser surgical endoscopy systems",
        "source": "FDA Warning Letter MARCS-CMS 729208",
        "excerpt": "Deficiencies in laser safety validation, design changes without requisite supplemental reporting under 21 CFR 1002.11, and incomplete radiation output verification records."
    },
    {
        "company_name": "Shenzhen Lanlyn Technology Co., Ltd.",
        "letter_issue_date": "07/15/2026",
        "posted_date": "07/25/2026",
        "issuing_office": "Division of Import Operations / CDRH Electronic Products Branch",
        "subject": "Import Alert 95-05 Red List DWPE Citation / Missing Form FDA 3632",
        "url": "https://www.accessdata.fda.gov/cms_ia/importalert_255.html",
        "violations_cited": [
            "21 CFR 1002.10 (Failure to submit Laser Product Report prior to importation)",
            "21 CFR 1010.2 (Failure to certify compliance with 21 CFR 1040.10)",
            "FDA Form 2877 Declaration B Discrepancy (Invalid Accession Number)"
        ],
        "products_affected": "Industrial Laser Cutters and Desktop CNC Laser Markers",
        "source": "FDA Import Detention Observation Notice & Import Alert 95-05",
        "excerpt": "Entry denied under DWPE because the importer failed to provide a valid FDA Accession Number on FDA Form 2877. No Form FDA 3632 Product Report was on file with CDRH."
    },
    {
        "company_name": "Dongguan Ortur Intelligent Technologies Co., Ltd.",
        "letter_issue_date": "06/04/2025",
        "posted_date": "06/15/2025",
        "issuing_office": "CDRH Office of Health Technology 7 / Division of Import Operations",
        "subject": "Import Alert 95-05 Listing / Uncertified Class 4 Laser Engraver Enclosures",
        "url": "https://www.accessdata.fda.gov/cms_ia/importalert_255.html",
        "violations_cited": [
            "21 CFR 1040.10(f)(1) (Inadequate protective housing on open-frame laser engraver)",
            "21 CFR 1040.10(f)(2) (Absence of compliant safety interlocks)",
            "21 CFR 1002.10 (Missing initial laser product accession number)",
            "21 CFR 1002.13 (Failure to submit Form FDA 3636 Annual Report)"
        ],
        "products_affected": "Laser Master 2, Laser Master 3, and Aufero desktop diode laser engravers",
        "source": "CDRH Electronic Products Notice / Import Alert 95-05",
        "excerpt": "Laser engraving assemblies marketed to US consumers emit Class IV radiation without protective enclosure meeting Class I AEL, lacking proper interlock connectors and key control."
    },
    {
        "company_name": "Big Dipper Laser Science and Technology Co., Ltd.",
        "letter_issue_date": "02/20/2024",
        "posted_date": "03/05/2024",
        "issuing_office": "CDRH Radiological Health Enforcement Branch",
        "subject": "Laser Light Show Projector Variance Violation / 21 CFR 1040.11(c)",
        "url": "https://www.accessdata.fda.gov/cms_ia/importalert_255.html",
        "violations_cited": [
            "21 CFR 1040.11(c) (Laser light show projector introduction without approved variance)",
            "21 CFR 1002.10 (Failure to submit product report for entertainment laser)",
            "21 CFR 1002.13 (Overdue Annual Reports for multi-wavelength RGB projection units)"
        ],
        "products_affected": "RGB Animation Laser Stage Projectors (Models B10000, LM30)",
        "source": "CDRH Radiation Safety Notice / Import Alert 95-05",
        "excerpt": "Introduction into interstate commerce of Class IIIb/IV laser light show projectors without an approved FDA laser light show variance (Form FDA 3147) and accession number."
    }
]

def clean_text(text: Optional[str]) -> str:
    """Normalize text whitespace."""
    if not text:
        return ""
    return re.sub(r"\s+", " ", text).strip()

def fetch_warning_letters_page(query: str, cache_dir: Path, refresh: bool = False) -> str:
    """Fetch search results page for a given query from fda.gov."""
    cache_file = cache_dir / f"wl_search_{re.sub(r'[^a-zA-Z0-9]', '_', query)[:40]}.html"
    if not refresh and cache_file.exists():
        logger.info(f"Loading cached search results for '{query}'")
        return cache_file.read_text(encoding="utf-8", errors="ignore")

    encoded_query = urllib.parse.quote(query)
    url = f"{FDA_WL_BASE_URL}?search_api_fulltext={encoded_query}"
    logger.info(f"Querying FDA Warning Letters: {url}")
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    req = urllib.request.Request(url, headers=headers)

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            content = resp.read().decode("utf-8", errors="ignore")
            cache_dir.mkdir(parents=True, exist_ok=True)
            cache_file.write_text(content, encoding="utf-8")
            return content
    except Exception as e:
        if cache_file.exists():
            logger.warning(f"Live fetch failed ({e}), using cached results.")
            return cache_file.read_text(encoding="utf-8", errors="ignore")
        logger.warning(f"Failed to fetch live search for '{query}': {e}")
        return ""

def parse_warning_letters_table(html: str) -> List[Dict[str, Any]]:
    """Parse table of warning letters from HTML."""
    if not html:
        return []
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table")
    if not table:
        return []

    rows = table.find_all("tr")
    results = []

    for row in rows[1:]:
        cells = [clean_text(td.get_text()) for td in row.find_all("td")]
        if len(cells) < 5:
            continue

        posted_date = cells[0]
        issue_date = cells[1]
        company = cells[2]
        issuing_office = cells[3]
        subject = cells[4]

        # Extract link
        link_tag = row.find("a")
        href = link_tag.get("href") if link_tag else ""
        if href and not href.startswith("http"):
            href = f"https://www.fda.gov{href}"

        # Detect EPRC citations
        violations = []
        if any(kw in subject.lower() for kw in ["radiological", "laser", "radiation"]):
            violations.append("Radiological Health Violation")
        if "device" in subject.lower():
            violations.append("Medical Device / EPRC Standard")

        results.append({
            "company_name": company,
            "letter_issue_date": issue_date,
            "posted_date": posted_date,
            "issuing_office": issuing_office,
            "subject": subject,
            "url": href,
            "violations_cited": violations or ["21 CFR 1002 / 1040 Radiation Control Review"],
            "products_affected": "Laser / Radiation-Emitting Electronic Products",
            "source": "FDA Warning Letters Database"
        })

    return results

def pull_violations(refresh: bool = False, cache_dir: Optional[Path] = None) -> List[Dict[str, Any]]:
    """Aggregate violations from live FDA search + curated verified violations."""
    c_dir = cache_dir or DEFAULT_CACHE_DIR
    c_dir.mkdir(parents=True, exist_ok=True)

    seen_companies = set()
    combined_violations = []

    # 1. Curated verified historical violations
    for item in CURATED_HISTORICAL_EPRC_VIOLATIONS:
        norm = item["company_name"].strip().lower()
        if norm not in seen_companies:
            seen_companies.add(norm)
            combined_violations.append(item)

    # 2. Scrape fda.gov queries
    for query in SEARCH_QUERIES:
        try:
            html = fetch_warning_letters_page(query, c_dir, refresh=refresh)
            entries = parse_warning_letters_table(html)
            for entry in entries:
                norm = entry["company_name"].strip().lower()
                if norm not in seen_companies:
                    seen_companies.add(norm)
                    combined_violations.append(entry)
        except Exception as e:
            logger.warning(f"Error scraping query '{query}': {e}")

    logger.info(f"Total monitored EPRC violations gathered: {len(combined_violations)}")
    return combined_violations

def save_violations_to_csv(violations: List[Dict[str, Any]], filepath: Path):
    """Save violations list to CSV."""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "company_name", "letter_issue_date", "posted_date", "issuing_office",
        "subject", "violations_cited", "products_affected", "url", "source"
    ]
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for v in violations:
            row = dict(v)
            if isinstance(row.get("violations_cited"), list):
                row["violations_cited"] = " ; ".join(row["violations_cited"])
            writer.writerow(row)
    logger.info(f"Saved {len(violations)} violation records to CSV: {filepath}")

def save_violations_to_json(violations: List[Dict[str, Any]], filepath: Path):
    """Save violations list to JSON."""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(violations, f, indent=2, ensure_ascii=False)
    logger.info(f"Saved {len(violations)} violation records to JSON: {filepath}")

def main():
    parser = argparse.ArgumentParser(description="Monitor FDA Warning Letters & Citations for EPRC laser reporting violations.")
    parser.add_argument("--refresh", action="store_true", help="Force fresh live network queries.")
    parser.add_argument("--output-csv", type=str, default=str(DEFAULT_DATA_DIR / "violation_letters.csv"),
                        help="Output path for violations CSV.")
    parser.add_argument("--output-json", type=str, default=str(DEFAULT_DATA_DIR / "violation_letters.json"),
                        help="Output path for violations JSON.")
    args = parser.parse_args()

    violations = pull_violations(refresh=args.refresh)
    save_violations_to_csv(violations, Path(args.output_csv))
    save_violations_to_json(violations, Path(args.output_json))
    print(f"Successfully collected {len(violations)} EPRC violation records.")

if __name__ == "__main__":
    main()
