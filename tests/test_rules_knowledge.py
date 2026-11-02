"""Unit tests for EPRC Knowledge Base and regulatory rules."""

import pytest
from pathlib import Path
import sys

desk_dir = Path(__file__).resolve().parent.parent
if str(desk_dir) not in sys.path:
    sys.path.insert(0, str(desk_dir))

from rules.knowledge_base import EPRCKnowledgeBase, get_knowledge_base

def test_knowledge_base_loading():
    kb = get_knowledge_base()
    assert kb is not None
    assert "statutory_authority" in kb.data
    assert "cfr_1002_1_table_1" in kb.data

def test_statutory_penalties():
    kb = get_knowledge_base()
    penalties = kb.civil_penalties
    assert penalties["per_violation_limit"] == 1100
    assert penalties["series_maximum_limit"] == 330000

def test_table_1_classes():
    kb = get_knowledge_base()
    classes = ["Class I", "Class IIa", "Class II", "Class IIIa", "Class IIIb", "Class IV"]
    for c in classes:
        reqs = kb.get_class_requirements(c)
        assert reqs["product_report_1002_10"] is True
        assert reqs["annual_report_1002_13"] is True

def test_class_safety_features():
    kb = get_knowledge_base()
    class_iv = kb.get_class_requirements("Class IV")
    assert "key_control" in class_iv["safety_features_required"]
    assert "remote_interlock_connector" in class_iv["safety_features_required"]
    assert "emission_indicator_with_delay" in class_iv["safety_features_required"]

def test_validate_safety_features_compliant():
    kb = get_knowledge_base()
    features = [
        "protective_housing",
        "safety_interlock_with_defeat_prevention",
        "remote_interlock_connector",
        "key_control",
        "emission_indicator_with_delay",
        "beam_attenuator",
        "danger_warning_logotype_label",
        "aperture_label"
    ]
    res = kb.validate_safety_features("Class IV", features)
    assert res["valid"] is True
    assert len(res["missing_features"]) == 0

def test_validate_safety_features_missing():
    kb = get_knowledge_base()
    # Missing key control and remote interlock
    features = ["protective_housing", "emission_indicator"]
    res = kb.validate_safety_features("Class IV", features)
    assert res["valid"] is False
    assert any("key_control" in mf for mf in res["missing_features"])

def test_laser_notices():
    kb = get_knowledge_base()
    notices = kb.laser_notices
    assert "Laser Notice 41" in notices
    assert "Laser Notice 42" in notices
    assert "Laser Notice 50" in notices
    assert "Laser Notice 54" in notices
    assert "Laser Notice 56" in notices

def test_form_2877_declarations():
    kb = get_knowledge_base()
    decl_b = kb.get_form_2877_declaration("B")
    assert "fda_accession_number" in decl_b["required_fields"]
    assert "model_number" in decl_b["required_fields"]

def test_submission_channels():
    kb = get_knowledge_base()
    channels = kb.submission_channels
    assert channels["primary_email"]["address"] == "RadHealthCustomerService@fda.hhs.gov"
    assert channels["filing_fee"]["amount"] == 0.0

def test_market_comparators():
    kb = get_knowledge_base()
    comps = kb.market_comparators
    assert comps["registrar_corp"]["initial_report"] == 995.0
    assert comps["eprc_laser_report_desk"]["initial_report"] == 495.0
    assert comps["eprc_laser_report_desk"]["annual_report"] == 295.0
