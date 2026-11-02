"""Unit tests for Warning Letters and 483 Violation Monitor."""

import pytest
from pathlib import Path
import sys

desk_dir = Path(__file__).resolve().parent.parent
if str(desk_dir) not in sys.path:
    sys.path.insert(0, str(desk_dir))

from violation_monitor import (
    parse_warning_letters_table, pull_violations,
    save_violations_to_csv, save_violations_to_json
)

SAMPLE_WL_TABLE_HTML = """
<table>
    <tr>
        <th>Posted Date</th>
        <th>Letter Issue Date</th>
        <th>Company Name</th>
        <th>Issuing Office</th>
        <th>Subject</th>
    </tr>
    <tr>
        <td>10/20/2026</td>
        <td>10/07/2026</td>
        <td>Olympus Medical Systems Corporation</td>
        <td>Center for Devices and Radiological Health</td>
        <td>CGMP/QSR/Medical Devices/Adulterated/Laser Systems</td>
    </tr>
    <tr>
        <td>08/05/2025</td>
        <td>06/27/2025</td>
        <td>Mectronic Medicale S.R.L.</td>
        <td>Center for Devices and Radiological Health</td>
        <td>Laser Radiation Control Violations / 21 CFR 1002.10</td>
    </tr>
</table>
"""

def test_parse_warning_letters_table():
    parsed = parse_warning_letters_table(SAMPLE_WL_TABLE_HTML)
    assert len(parsed) == 2
    assert parsed[0]["company_name"] == "Olympus Medical Systems Corporation"
    assert parsed[0]["letter_issue_date"] == "10/07/2026"
    assert parsed[1]["company_name"] == "Mectronic Medicale S.R.L."
    assert "Radiological Health Violation" in parsed[1]["violations_cited"]

def test_pull_violations():
    violations = pull_violations(refresh=False)
    assert len(violations) >= 5

    names = [v["company_name"] for v in violations]
    assert any("Mectronic Medicale" in n for n in names)
    assert any("Ortur" in n for n in names)
    assert any("Lanlyn" in n for n in names)

def test_save_violations_files(tmp_path):
    violations = pull_violations(refresh=False)
    csv_path = tmp_path / "violations.csv"
    json_path = tmp_path / "violations.json"

    save_violations_to_csv(violations, csv_path)
    save_violations_to_json(violations, json_path)

    assert csv_path.exists()
    assert json_path.exists()
    assert csv_path.stat().st_size > 0
    assert json_path.stat().st_size > 0
