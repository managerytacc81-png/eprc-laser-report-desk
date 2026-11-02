"""Unit tests for Import Alert 95-04 and 95-05 prospect harvester."""

import pytest
from pathlib import Path
import sys

desk_dir = Path(__file__).resolve().parent.parent
if str(desk_dir) not in sys.path:
    sys.path.insert(0, str(desk_dir))

from prospect_harvester import (
    clean_text, categorize_laser_product, extract_models,
    parse_import_alert_html, harvest_prospects, save_to_csv, save_to_json
)

SAMPLE_ALERT_HTML = """
<html>
<body>
    <div class="center"><h4>CHINA</h4></div>
    <hr/>
    <div class="div-info">
        <div class="div-name floatleft">Test Laser Tech Ltd.</div>
        <div class="div-name floatright">Date Published : 04/15/2025</div>
        <div class="clear">High-Tech Industrial Park, Shenzhen, Guangdong CHINA</div>
    </div>
    <div>95 R - - FE Laser Cutter, Material Processing Laser Products Date Published: 04/15/2025</div>
    <p class="clear">Notes: Product Models: TL-1000, TL-2000, PRO-MAX</p>
    <div class="div-info">
        <div class="div-name floatleft">Older Laser Corp</div>
        <div class="div-name floatright">Date Published : 05/10/2021</div>
        <div class="clear">Industrial Zone, Shanghai CHINA</div>
    </div>
    <div>95 R - - ES Laser Pointer Date Published: 05/10/2021</div>
</body>
</html>
"""

def test_clean_text():
    assert clean_text("  hello   world \n \t ") == "hello world"
    assert clean_text(None) == ""

def test_categorize_laser_product():
    assert categorize_laser_product("Laser Cutter, Material Processing") == "Laser Cutter / CNC"
    assert categorize_laser_product("Handheld Laser Welder") == "Laser Welder"
    assert categorize_laser_product("Desktop Laser Engraver and Marker") == "Laser Engraver / Marker"
    assert categorize_laser_product("Surveying Leveling Alignment Laser") == "Laser Level / Surveying (SLA)"
    assert categorize_laser_product("RGB Laser Light Show Projector") == "Laser Light Show / Projector"
    assert categorize_laser_product("Laser Pointer Key Chain") == "Laser Pointer / Aiming Device"
    assert categorize_laser_product("Therapeutic Medical Laser") == "Medical / Veterinary Laser"

def test_extract_models():
    text = "Notes: Product Models: AKJ1530FR, AK60C, AKQ-1000, AKH-20"
    models = extract_models(text)
    assert "AKJ1530FR" in models
    assert "AK60C" in models
    assert "AKH-20" in models

def test_parse_import_alert_html():
    records = parse_import_alert_html(SAMPLE_ALERT_HTML, "95-05")
    assert len(records) == 2

    r1 = records[0]
    assert r1["firm_name"] == "Test Laser Tech Ltd."
    assert r1["country"] == "CHINA"
    assert r1["date_listed"] == "04/15/2025"
    assert r1["year_listed"] == 2025
    assert r1["is_recent_2025_2026"] is True
    assert r1["category"] == "Laser Cutter / CNC"
    assert "TL-1000" in r1["models"]

    r2 = records[1]
    assert r2["firm_name"] == "Older Laser Corp"
    assert r2["year_listed"] == 2021
    assert r2["is_recent_2025_2026"] is False

def test_save_csv_and_json(tmp_path):
    records = parse_import_alert_html(SAMPLE_ALERT_HTML, "95-05")
    csv_file = tmp_path / "test_out.csv"
    json_file = tmp_path / "test_out.json"

    save_to_csv(records, csv_file)
    save_to_json(records, json_file)

    assert csv_file.exists()
    assert json_file.exists()
    assert csv_file.stat().st_size > 0
    assert json_file.stat().st_size > 0
