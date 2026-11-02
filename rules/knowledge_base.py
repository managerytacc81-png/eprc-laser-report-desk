"""Knowledge Base reader and validation logic for FDA EPRC Laser regulations.

Encodes 21 CFR 1002.1 Table 1, Laser Notices 41/42/50/54/56, FDA Form 2877,
submission channels, and statutory penalties.
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional

RULES_FILE = Path(__file__).resolve().parent / "eprc_knowledge.json"

class EPRCKnowledgeBase:
    def __init__(self, json_path: Optional[Path] = None):
        self.path = json_path or RULES_FILE
        with open(self.path, "r", encoding="utf-8") as f:
            self.data: Dict[str, Any] = json.load(f)

    @property
    def statutory_authority(self) -> Dict[str, Any]:
        return self.data["statutory_authority"]

    @property
    def civil_penalties(self) -> Dict[str, Any]:
        return self.data["statutory_authority"]["civil_penalties"]

    @property
    def table_1(self) -> Dict[str, Any]:
        return self.data["cfr_1002_1_table_1"]

    @property
    def laser_notices(self) -> Dict[str, Any]:
        return self.data["laser_notices"]

    @property
    def form_2877(self) -> Dict[str, Any]:
        return self.data["form_fda_2877"]

    @property
    def submission_channels(self) -> Dict[str, Any]:
        return self.data["submission_channels"]

    @property
    def market_comparators(self) -> Dict[str, Any]:
        return self.data["market_comparators"]

    def get_class_requirements(self, laser_class: str) -> Dict[str, Any]:
        """Return reporting requirements and required safety features for a given laser class."""
        classes = self.data["cfr_1002_1_table_1"]["classes"]
        # Normalize class name
        norm = laser_class.strip()
        for k, v in classes.items():
            if k.lower() == norm.lower():
                return v
        # Try fuzzy match
        if "iv" in norm.lower() or "4" in norm.lower():
            return classes["Class IV"]
        if "iiib" in norm.lower() or "3b" in norm.lower():
            return classes["Class IIIb"]
        if "iiia" in norm.lower() or "3r" in norm.lower() or "3a" in norm.lower():
            return classes["Class IIIa"]
        if "iia" in norm.lower() or "2a" in norm.lower():
            return classes["Class IIa"]
        if "ii" in norm.lower() or "2" in norm.lower():
            return classes["Class II"]
        if "i" in norm.lower() or "1" in norm.lower():
            return classes["Class I"]
        raise ValueError(f"Unknown laser class: '{laser_class}'. Must be Class I, IIa, II, IIIa, IIIb, IV, or Medical Laser Products.")

    def validate_safety_features(self, laser_class: str, provided_features: List[str]) -> Dict[str, Any]:
        """Check if provided safety features satisfy 21 CFR 1040.10 for the given laser class."""
        reqs = self.get_class_requirements(laser_class)
        mandatory = set(reqs.get("safety_features_required", []))
        provided = set(f.lower().strip().replace(" ", "_").replace("-", "_") for f in provided_features)

        missing = []
        for req in mandatory:
            # check if any provided feature contains the key tokens
            tokens = req.split("_")
            matched = any(all(tok in pf for tok in tokens if len(tok) > 3) for pf in provided)
            if not matched and req not in provided:
                missing.append(req)

        return {
            "valid": len(missing) == 0,
            "laser_class": laser_class,
            "mandatory_features": list(mandatory),
            "provided_features": list(provided),
            "missing_features": missing
        }

    def get_form_2877_declaration(self, declaration_code: str) -> Dict[str, Any]:
        """Return Form 2877 declaration description and requirements."""
        code = declaration_code.upper().strip()
        decls = self.data["form_fda_2877"]["declarations"]
        if code in decls:
            return decls[code]
        raise ValueError(f"Invalid declaration code '{declaration_code}'. Must be A, B, C, or D.")

_kb_instance = None

def get_knowledge_base() -> EPRCKnowledgeBase:
    global _kb_instance
    if _kb_instance is None:
        _kb_instance = EPRCKnowledgeBase()
    return _kb_instance
