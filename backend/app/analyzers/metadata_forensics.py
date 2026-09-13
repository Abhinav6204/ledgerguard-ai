"""
LedgerGuard AI — Document Forensic Metadata & Behavioral Analyzer
Inspects PDF binary metadata, producer anomalies, post-export modification trails, and urgency pressure tactics.
"""

import re
from typing import Dict, Any, List
from app.models.schemas import ForensicFlag, FlagCategory, FlagSeverity

class MetadataForensics:
    """Detects graphic editor tampering, metadata manipulation, and social engineering language."""

    SUSPICIOUS_PRODUCERS = [
        "photoshop", "gimp", "canva", "coreldraw", "pdfedit", "illustrator",
        "inkscape", "foxit phantom", "nitro pro", "sejda", "smallpdf"
    ]

    LEGITIMATE_PRODUCERS = [
        "quickbooks", "netsuite", "sap", "xero", "stripe", "freshbooks", 
        "zoho", "reportlab", "wkhtmltopdf", "chrome", "headlesschrome", "weasyprint"
    ]

    URGENCY_TRIGGERS = [
        r"(?i)\bimmediate(?:\s+wire|\s+payment|\s+remittance)\b",
        r"(?i)\burgent\s+action\s+required\b",
        r"(?i)\bdo\s+not\s+contact\s+via\s+phone\b",
        r"(?i)\bconfidential\s+wire\s+instructions\b",
        r"(?i)\baccount\s+recently\s+updated\b",
        r"(?i)\bpenalt(?:y|ies)\s+for\s+delay\b",
        r"(?i)\blawsuit\s+pending\b",
        r"(?i)\bfinal\s+notice\s+before\s+suspension\b"
    ]

    @classmethod
    def audit_metadata_and_text(cls, metadata: Dict[str, Any], raw_text: str) -> List[ForensicFlag]:
        flags: List[ForensicFlag] = []

        creator = (metadata.get("creator") or "").lower()
        producer = (metadata.get("producer") or "").lower()
        combined_tools = f"{creator} {producer}"

        # 1. Suspicious Graphic Editor Detection
        for susp in cls.SUSPICIOUS_PRODUCERS:
            if susp in combined_tools:
                flags.append(ForensicFlag(
                    category=FlagCategory.METADATA_TAMPERING,
                    severity=FlagSeverity.HIGH,
                    title="Document Generated via Graphic Manipulation Software",
                    description=(
                        f"PDF metadata identifies creation tool '{susp.capitalize()}' ({creator or producer}). "
                        "Legitimate enterprise invoices originate from accounting/ERP systems, not image manipulation editors."
                    ),
                    recommendation="Inspect invoice for digitally spliced bank coordinates or modified total figures."
                ))
                break

        # 2. Urgent / Coercive Social Engineering Language
        for trigger in cls.URGENCY_TRIGGERS:
            match = re.search(trigger, raw_text)
            if match:
                flags.append(ForensicFlag(
                    category=FlagCategory.PRESSURE_TACTIC,
                    severity=FlagSeverity.MEDIUM,
                    title="Urgency / Psychological Pressure Tactic Detected",
                    description=(
                        f"The invoice contains coercive language: '{match.group(0)}'. "
                        "Scammers frequently use extreme urgency to bypass standard internal approval workflows."
                    ),
                    recommendation="Enforce standard dual-approval payment processing without expediting."
                ))
                break

        return flags
