"""End-to-End integration tests for FDA EPRC Laser Report Desk."""

import os
import json
import pytest
from pathlib import Path
import sys

desk_dir = Path(__file__).resolve().parent.parent
if str(desk_dir) not in sys.path:
    sys.path.insert(0, str(desk_dir))

DATA_DIR = desk_dir / "data"

# Canonical outbox location (configurable via env var)
_DEFAULT_OUTBOX_DIR = Path("/home/user/revenue-eval/outbox")
_OUTBOX_DIR = Path(os.environ.get("REVENUE_OUTBOX_DIR", str(_DEFAULT_OUTBOX_DIR)))

# Desktop path kept as optional secondary location
_DESKTOP_DIR = Path("/home/user/Desktop/REVENUE_ACTIONS_TONIGHT")


def _resolve_artifact(filename: str) -> Path:
    """Return the path to an artifact, preferring the canonical outbox location.

    Resolution order:
    1. ``$REVENUE_OUTBOX_DIR/<filename>`` (or the default outbox dir)
    2. ``~/Desktop/REVENUE_ACTIONS_TONIGHT/<filename>`` (legacy/secondary)

    Returns the first path that exists, falling back to the canonical path so
    that assertion failures report the expected canonical location.
    """
    canonical = _OUTBOX_DIR / filename
    if canonical.exists():
        return canonical
    desktop = _DESKTOP_DIR / filename
    if desktop.exists():
        return desktop
    # Default to canonical so error messages point at the right place
    return canonical


DESKTOP_OUTBOX = _resolve_artifact("eprc-laser-report-desk_OUTBOX.md")
DESKTOP_SCRIPT = _resolve_artifact("send_eprc_laser_outbox.py")

def test_enriched_leads_count():
    leads_file = DATA_DIR / "enriched_leads.json"
    assert leads_file.exists(), "enriched_leads.json must exist"
    with open(leads_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    leads = data["leads"]
    assert len(leads) >= 15, f"Expected at least 15 verified leads, found {len(leads)}"

    # Check required fields
    for lead in leads:
        assert lead["contact_name"], "Missing contact name"
        assert lead["contact_title"], "Missing contact title"
        assert lead["email"], "Missing email"
        assert "@" in lead["email"], "Invalid email format"
        assert lead["phone"], "Missing phone"
        assert lead["alert_id"] in ["95-04", "95-05"], "Invalid alert ID"
        assert lead["alert_date"], "Missing alert date"
        assert lead["products_cited"], "Missing products cited"
        assert lead["mx_valid"] is True, f"MX record must be valid for {lead['domain']}"

def test_amazon_brands_count():
    amazon_file = DATA_DIR / "amazon_laser_brands.json"
    assert amazon_file.exists(), "amazon_laser_brands.json must exist"
    with open(amazon_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    brands = data["brands"]
    assert len(brands) >= 6, f"Expected at least 6 Amazon laser brands, found {len(brands)}"

    for b in brands:
        assert b["brand_name"]
        assert b["email"]
        assert b["products_on_amazon"]
        assert b["amazon_risk_factors"]

def test_desktop_outbox_exists_and_populated():
    assert DESKTOP_OUTBOX.exists(), "Desktop outbox markdown file must exist"
    content = DESKTOP_OUTBOX.read_text(encoding="utf-8")
    assert len(content) > 50000, "Outbox markdown should be comprehensive"
    assert "mailto:" in content, "Must include 1-click mailto links"
    assert "$495" in content, "Must cite $495 commercial wedge pricing"
    assert "Import Alert" in content, "Must reference import alerts"
    assert "201689020" in content, "Must reference Amazon policy 201689020"

def test_desktop_send_script_exists_and_executable():
    assert DESKTOP_SCRIPT.exists(), "Desktop send script must exist"
    assert os.access(DESKTOP_SCRIPT, os.X_OK), "Script should be executable"
    script_text = DESKTOP_SCRIPT.read_text(encoding="utf-8")
    assert "def main():" in script_text
    assert "--dry-run" in script_text
    assert "--open-mailto" in script_text
    assert "--send-smtp" in script_text
