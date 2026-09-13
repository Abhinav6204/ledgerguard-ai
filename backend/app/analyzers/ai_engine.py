"""
LedgerGuard AI — Dual-Engine LLM Inference & Forensic Synthesis Pipeline
Integrates Groq (LLaMA-3.3-70B) and Google Gemini (Gemini-1.5-Flash) with deterministic fallback.
"""

import httpx
import json
import logging
from typing import Dict, Any, List, Tuple
from app.config import settings
from app.models.schemas import RiskLevel, ForensicFlag, FlagSeverity
from app.core.security import InputSanitizer

logger = logging.getLogger("ledgerguard.ai")

class ForensicAIEngine:
    """Orchestrates multi-model reasoning and deterministic risk computation."""

    @classmethod
    async def analyze_invoice(
        cls, 
        parsed_data: Dict[str, Any], 
        flags: List[ForensicFlag]
    ) -> Tuple[int, RiskLevel, str, str]:
        """
        Computes composite risk score and generates executive verdict.
        Returns: (risk_score, risk_level, verdict_title, ai_rationale)
        """
        # 1. Compute Base Heuristic Risk Score (0 - 100)
        score = 0
        severity_weights = {
            FlagSeverity.CRITICAL: 85,
            FlagSeverity.HIGH: 35,
            FlagSeverity.MEDIUM: 15,
            FlagSeverity.LOW: 5,
            FlagSeverity.INFO: 0
        }

        for flag in flags:
            score += severity_weights.get(flag.severity, 0)

        # Cap score between 0 and 100
        score = min(100, max(0, score))

        # Determine Risk Level
        if score >= 80:
            level = RiskLevel.CRITICAL_FRAUD
            verdict = "CRITICAL RISK: HIGH LIKELIHOOD OF FRAUDULENT INVOICE"
        elif score >= 50:
            level = RiskLevel.HIGH_RISK
            verdict = "HIGH RISK: MATERIAL ANOMALIES DETECTED"
        elif score >= 25:
            level = RiskLevel.SUSPICIOUS
            verdict = "SUSPICIOUS: SECONDARY RECONCILIATION REQUIRED"
        elif score >= 10:
            level = RiskLevel.LOW_RISK
            verdict = "LOW RISK: MINOR NON-CRITICAL VARIANCES"
        else:
            level = RiskLevel.CLEAN
            verdict = "CLEAN: INVOICE VERIFIED & AUDIT PASSED"

        # 2. Attempt Deep Reasoning via LLM if credentials present
        ai_rationale = await cls._try_llm_reasoning(parsed_data, flags, score, level)
        if not ai_rationale:
            # Deterministic fallback synthesis
            ai_rationale = cls._synthesize_local_rationale(parsed_data, flags, score, level)

        return score, level, verdict, ai_rationale

    @classmethod
    async def _try_llm_reasoning(
        cls, 
        parsed_data: Dict[str, Any], 
        flags: List[ForensicFlag],
        score: int,
        level: RiskLevel
    ) -> str:
        """Attempts Groq or Gemini inference with strict timeout and fallback."""
        raw_text = parsed_data.get("raw_text", "")
        fenced_input = InputSanitizer.sanitize_text_for_llm(raw_text[:4000])

        flag_summaries = "\n".join([f"- [{f.severity.value}] {f.title}: {f.description}" for f in flags])

        prompt = f"""
You are the Chief Financial Fraud Forensics AI for LedgerGuard.
Analyze the following invoice and forensic flags to produce a crisp 3-sentence executive summary.

Identified Forensic Flags:
{flag_summaries if flag_summaries else "None. Document passed all deterministic checks."}

Invoice Snippet:
{fenced_input}

Output format:
1. Executive Verdict (State whether payment should proceed or be blocked).
2. Key Risk Drivers (Summarize bank, math, or entity discrepancies).
3. Recommended Action for Accounts Payable Treasury team.
Keep it strictly under 100 words.
"""

        # Try Groq first (Ultra-Fast)
        if settings.GROQ_API_KEY:
            try:
                async with httpx.AsyncClient(timeout=4.0) as client:
                    resp = await client.post(
                        "https://api.groq.com/openai/v1/chat/completions",
                        headers={
                            "Authorization": f"Bearer {settings.GROQ_API_KEY}",
                            "Content-Type": "application/json"
                        },
                        json={
                            "model": "llama-3.3-70b-versatile",
                            "messages": [
                                {"role": "system", "content": "You are a specialized corporate finance security forensic auditor."},
                                {"role": "user", "content": prompt}
                            ],
                            "max_tokens": 200,
                            "temperature": 0.1
                        }
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        return data["choices"][0]["message"]["content"].strip()
            except Exception as e:
                logger.warning(f"Groq inference failed or timed out: {e}")

        # Try Gemini fallback
        if settings.GEMINI_API_KEY:
            try:
                async with httpx.AsyncClient(timeout=4.0) as client:
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={settings.GEMINI_API_KEY}"
                    resp = await client.post(
                        url,
                        headers={"Content-Type": "application/json"},
                        json={
                            "contents": [{"parts": [{"text": prompt}]}],
                            "generationConfig": {"maxOutputTokens": 200, "temperature": 0.1}
                        }
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        return data["candidates"][0]["content"]["parts"][0]["text"].strip()
            except Exception as e:
                logger.warning(f"Gemini inference failed or timed out: {e}")

        return ""

    @classmethod
    def _synthesize_local_rationale(
        cls, 
        parsed_data: Dict[str, Any], 
        flags: List[ForensicFlag],
        score: int,
        level: RiskLevel
    ) -> str:
        """Deterministic, highly articulate forensic rationale generator."""
        vendor_name = parsed_data.get("vendor", {}).name if hasattr(parsed_data.get("vendor"), "name") else "the vendor"
        total = parsed_data.get("total_amount", 0.0)

        critical_flags = [f for f in flags if f.severity in [FlagSeverity.CRITICAL, FlagSeverity.HIGH]]

        if level == RiskLevel.CRITICAL_FRAUD:
            reasons = "; ".join([f.title for f in critical_flags[:2]])
            return (
                f"PAYMENT EMBARGO RECOMMENDED: Invoice claims ${total:,.2f} for {vendor_name} but exhibits severe security breaches ({reasons}). "
                "Treasury must immediately freeze electronic disbursement and execute verbal out-of-band verification via known phone records."
            )
        elif level == RiskLevel.HIGH_RISK or level == RiskLevel.SUSPICIOUS:
            return (
                f"CONDITIONAL APPROVAL: Multiple anomalies flagged totaling risk rating of {score}/100 for {vendor_name}. "
                "Line items and banking coordinates require manual controller sign-off prior to ACH or wire submission."
            )
        else:
            return (
                f"AUDIT PASSED: Mathematical balances, routing parameters, and entity metadata for {vendor_name} reconcile with company accounting baselines. "
                "Invoice is cleared for standard payment scheduling."
            )
