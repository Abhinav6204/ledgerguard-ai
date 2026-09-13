"""
LedgerGuard AI — Precision Financial Math Auditor
Detects altered financial line items, phantom fees, tax miscalculations, and rounding discrepancies.
"""

from typing import List, Dict, Any, Tuple
from app.models.schemas import ForensicFlag, FlagCategory, FlagSeverity

class MathAuditor:
    """Verifies mathematical consistency across all extracted financial figures."""

    TOLERANCE = 0.05  # Allow 5 cents rounding margin

    @classmethod
    def audit_figures(cls, parsed_data: Dict[str, Any]) -> Tuple[bool, List[ForensicFlag]]:
        flags: List[ForensicFlag] = []
        is_verified = True

        subtotal = parsed_data.get("subtotal", 0.0)
        tax = parsed_data.get("tax_amount", 0.0)
        total = parsed_data.get("total_amount", 0.0)
        line_items = parsed_data.get("line_items", [])
        calc_subtotal = parsed_data.get("calculated_subtotal", 0.0)

        # 1. Total Balance Check: Subtotal + Tax vs Total
        if subtotal > 0 and total > 0:
            expected_total = subtotal + tax
            diff = abs(expected_total - total)
            if diff > cls.TOLERANCE:
                is_verified = False
                flags.append(ForensicFlag(
                    category=FlagCategory.MATH_DISCREPANCY,
                    severity=FlagSeverity.HIGH,
                    title="Invoice Grand Total Mathematical Mismatch",
                    description=(
                        f"Subtotal (${subtotal:,.2f}) + Tax (${tax:,.2f}) evaluates to ${expected_total:,.2f}, "
                        f"which does not reconcile with the printed Total of ${total:,.2f} (Discrepancy: ${diff:,.2f})."
                    ),
                    recommendation="Do not authorize payment until vendor resubmits a reconciled statement."
                ))

        # 2. Line Item Sum vs Stated Subtotal
        if line_items and subtotal > 0 and calc_subtotal > 0:
            diff_subtotal = abs(calc_subtotal - subtotal)
            if diff_subtotal > cls.TOLERANCE:
                is_verified = False
                flags.append(ForensicFlag(
                    category=FlagCategory.MATH_DISCREPANCY,
                    severity=FlagSeverity.MEDIUM,
                    title="Line Item Sum Discrepancy",
                    description=(
                        f"Calculated sum of {len(line_items)} extracted line items is ${calc_subtotal:,.2f}, "
                        f"differing from the stated subtotal of ${subtotal:,.2f}."
                    ),
                    recommendation="Review individual line item rates and quantities for hidden unauthorized charges."
                ))

        # 3. Sanity check for zero or negative values
        if total < 0 or subtotal < 0:
            is_verified = False
            flags.append(ForensicFlag(
                category=FlagCategory.MATH_DISCREPANCY,
                severity=FlagSeverity.CRITICAL,
                title="Negative Financial Total Detected",
                description="The invoice states negative balance values without appropriate credit memo documentation.",
                recommendation="Halt processing immediately. Verify whether document is a credit memo or fraudulent charge."
            ))

        return is_verified, flags
