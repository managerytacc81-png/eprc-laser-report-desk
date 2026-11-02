#!/usr/bin/env python3
"""FDA Import Alert 95-04 and 95-05 Red List Prospect Harvester.

Scrapes FDA Import Alert 95-04 (Laser pointers, levels, light shows, SLA products)
and 95-05 (Electronic products failing to comply with performance standards/certification)
Red Lists into structured CSV/JSON. Flags firms newly listed in 2025-2026 with
US-relevant products.
"""

import os
import sys
import re
import csv
import json
import logging
import argparse
import urllib.request
from pathlib import Path
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("prospect_harvester")

DEFAULT_DATA_DIR = Path(__file__).resolve().parent / "data"
DEFAULT_CACHE_DIR = Path(__file__).resolve().parent / ".cache"

IMPORT_ALERTS = {
    "95-04": {
        "alert_number": "95-04",
        "url": "https://www.accessdata.fda.gov/cms_ia/importalert_254.html",
        "title": "Detention Without Physical Examination Of Laser Pointers, Laser Gunsights, Laser Levels, Laser Light Shows, Laser Pointer Key Chains, & Similar Products",
        "primary_focus": "Laser Pointers, Surveying/Leveling/Alignment (SLA), Laser Light Shows"
    },
    "95-05": {
        "alert_number": "95-05",
        "url": "https://www.accessdata.fda.gov/cms_ia/importalert_255.html",
        "title": "Detention Without Physical Examination of Electronic Products that Fail to Comply with Performance Standards or to Have Required Certification",
        "primary_focus": "Laser Cutters, Laser Welders, Industrial/Consumer Engravers, Medical Lasers"
    }
}

def clean_text(text: Optional[str]) -> str:
    """Normalize whitespace and strip text."""
    if not text:
        return ""
    return re.sub(r"\s+", " ", text).strip()

def categorize_laser_product(product_text: str) -> str:
    """Classify laser product description into industry category."""
    p_lower = product_text.lower()
    if any(k in p_lower for k in ["cutter", "cutting"]):
        return "Laser Cutter / CNC"
    if any(k in p_lower for k in ["welder", "welding"]):
        return "Laser Welder"
    if any(k in p_lower for k in ["marker", "engraver", "marking", "engraving"]):
        return "Laser Engraver / Marker"
    if any(k in p_lower for k in ["level", "surveying", "alignment", "geodimeter", "ranging"]):
        return "Laser Level / Surveying (SLA)"
    if any(k in p_lower for k in ["light show", "projector", "stage lighting", "display"]):
        return "Laser Light Show / Projector"
    if any(k in p_lower for k in ["pointer", "gunsight", "key chain"]):
        return "Laser Pointer / Aiming Device"
    if any(k in p_lower for k in ["medical", "therapy", "dental", "veterinary", "surgical"]):
        return "Medical / Veterinary Laser"
    if any(k in p_lower for k in ["scientific", "laboratory", "spectroscopy"]):
        return "Scientific / Laboratory Laser"
    return "General Purpose Laser Product"

def extract_models(text: str) -> List[str]:
    """Extract model numbers mentioned in notes or descriptions."""
    models = []
    # Match Product Models: ...
    m = re.findall(r"Product Models:\s*([^;<\n]+)", text, re.IGNORECASE)
    for match in m:
        parts = [clean_text(p) for p in match.split(",")]
        for p in parts:
            if p and len(p) < 35:
                models.append(p)
    return list(dict.fromkeys(models))

def fetch_html(url: str, cache_file: Path, refresh: bool = False) -> str:
    """Fetch HTML from URL or local cache."""
    if not refresh and cache_file.exists():
        logger.info(f"Loading cached HTML from {cache_file.name}")
        return cache_file.read_text(encoding="utf-8", errors="ignore")

    logger.info(f"Fetching live URL: {url}")
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            content = resp.read().decode("utf-8", errors="ignore")
            cache_file.parent.mkdir(parents=True, exist_ok=True)
            cache_file.write_text(content, encoding="utf-8")
            return content
    except Exception as e:
        if cache_file.exists():
            logger.warning(f"Fetch failed ({e}), falling back to cache {cache_file}")
            return cache_file.read_text(encoding="utf-8", errors="ignore")
        raise RuntimeError(f"Failed to fetch {url} and no cache exists: {e}")

def parse_import_alert_html(html: str, alert_id: str) -> List[Dict[str, Any]]:
    """Parse Import Alert HTML into list of structured firm records."""
    soup = BeautifulSoup(html, "html.parser")
    current_country = "GLOBAL"
    records = []

    # Traverse main content nodes
    elements = soup.find_all(["div", "hr"])
    for el in elements:
        # Detect country section header
        if el.name == "div" and "center" in el.get("class", []):
            h4 = el.find("h4")
            if h4:
                country_text = clean_text(h4.get_text())
                if country_text and not any(kw in country_text for kw in ["Red List", "Import Alert", "Detention"]):
                    current_country = country_text.upper()

        elif el.name == "div" and "div-info" in el.get("class", []):
            name_div = el.find("div", class_=lambda c: c and "floatleft" in c)
            date_div = el.find("div", class_=lambda c: c and "floatright" in c)
            addr_div = el.find("div", class_="clear")

            firm_name = clean_text(name_div.get_text()) if name_div else "Unknown Firm"
            date_raw = clean_text(date_div.get_text()) if date_div else ""
            date_match = re.search(r"(\d{2}/\d{2}/\d{4})", date_raw)
            date_listed = date_match.group(1) if date_match else date_raw.replace("Date Published :", "").strip()

            address = clean_text(addr_div.get_text()) if addr_div else ""

            # Extract products and model numbers from sibling tags until next entry
            product_lines = []
            models_collected = []
            pac_codes = []

            sibling = el.find_next_sibling()
            while sibling:
                classes = sibling.get("class") or []
                if sibling.name == "div" and ("div-info" in classes or "center" in classes):
                    break
                if sibling.name == "hr":
                    break

                text = clean_text(sibling.get_text())
                if text:
                    # Look for PAC / Industry codes
                    pac_match = re.search(r"\b(95\s*R\s*-\s*-\s*[A-Z]{2}|\d{2}\s*-\s*-\s*-\s*--)\b", text)
                    if pac_match:
                        pac_codes.append(pac_match.group(1))

                    if any(kw in text for kw in ["Desc:", "Notes:", "Product Models:", "Laser", "Projector", "Light"]):
                        product_lines.append(text)
                    models_collected.extend(extract_models(text))

                sibling = sibling.find_next_sibling()

            # Determine year
            year = 0
            if date_listed and len(date_listed) >= 4:
                try:
                    year = int(date_listed.split("/")[-1])
                except ValueError:
                    pass

            is_recent = year in (2025, 2026)
            product_desc = " ; ".join(product_lines) if product_lines else "Laser Products / Electronic Radiation Emitting Products"
            category = categorize_laser_product(product_desc)

            # Determine US relevance
            # In EPRC, any foreign or domestic firm on 95-04/95-05 attempted to import into US
            # or sells consumer/industrial laser equipment targeting US buyers.
            us_relevant = True

            records.append({
                "alert_id": alert_id,
                "country": current_country,
                "firm_name": firm_name,
                "date_listed": date_listed,
                "year_listed": year,
                "is_recent_2025_2026": is_recent,
                "address": address,
                "category": category,
                "product_description": product_desc[:500],
                "models": ", ".join(models_collected) if models_collected else "Not specified",
                "pac_codes": ", ".join(dict.fromkeys(pac_codes)),
                "us_relevant": us_relevant,
                "action_type": "DWPE (Detention Without Physical Examination)",
                "statutory_charge": "21 CFR 1002.10 (Missing Product Report) / 21 CFR 1010.2 (Uncertified Laser Product)"
            })

    return records

def harvest_prospects(refresh: bool = False, min_year: int = 2025, cache_dir: Optional[Path] = None) -> List[Dict[str, Any]]:
    """Scrape and combine prospects from 95-04 and 95-05."""
    c_dir = cache_dir or DEFAULT_CACHE_DIR
    c_dir.mkdir(parents=True, exist_ok=True)
    all_records = []

    for alert_id, cfg in IMPORT_ALERTS.items():
        cache_file = c_dir / f"ia_{alert_id.replace('-', '_')}.html"
        html = fetch_html(cfg["url"], cache_file, refresh=refresh)
        records = parse_import_alert_html(html, alert_id)
        logger.info(f"Parsed {len(records)} entries from Import Alert {alert_id}")
        all_records.extend(records)

    logger.info(f"Total entries across all alerts: {len(all_records)}")
    recent_count = sum(1 for r in all_records if r.get("year_listed", 0) >= min_year)
    logger.info(f"Entries listed in {min_year}+: {recent_count}")
    return all_records

def save_to_csv(records: List[Dict[str, Any]], filepath: Path):
    """Write records to CSV."""
    if not records:
        logger.warning("No records to write.")
        return
    filepath.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "alert_id", "country", "firm_name", "date_listed", "year_listed",
        "is_recent_2025_2026", "category", "product_description", "models",
        "address", "pac_codes", "us_relevant", "action_type", "statutory_charge"
    ]
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(records)
    logger.info(f"Saved {len(records)} records to CSV: {filepath}")

def save_to_json(records: List[Dict[str, Any]], filepath: Path):
    """Write records to JSON."""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)
    logger.info(f"Saved {len(records)} records to JSON: {filepath}")

def main():
    parser = argparse.ArgumentParser(description="Harvest FDA Import Alert 95-04 and 95-05 Red Lists.")
    parser.add_argument("--refresh", action="store_true", help="Force refresh from FDA live URLs.")
    parser.add_argument("--min-year", type=int, default=2025, help="Minimum year to flag as recent (default: 2025).")
    parser.add_argument("--output-csv", type=str, default=str(DEFAULT_DATA_DIR / "import_alerts_redlist.csv"),
                        help="Output path for CSV.")
    parser.add_argument("--output-json", type=str, default=str(DEFAULT_DATA_DIR / "import_alerts_redlist.json"),
                        help="Output path for JSON.")
    parser.add_argument("--recent-only", action="store_true", help="Filter output to recent 2025-2026 entries only.")
    args = parser.parse_args()

    records = harvest_prospects(refresh=args.refresh, min_year=args.min_year)
    if args.recent_only:
        records = [r for r in records if r.get("year_listed", 0) >= args.min_year]
        logger.info(f"Filtered down to {len(records)} recent records.")

    save_to_csv(records, Path(args.output_csv))
    save_to_json(records, Path(args.output_json))
    print(f"Successfully harvested {len(records)} records from Import Alerts 95-04 and 95-05.")

if __name__ == "__main__":
    main()
