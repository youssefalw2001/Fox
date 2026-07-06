#!/usr/bin/env python3
from __future__ import annotations

from typing import Any, Dict, Iterable, List


def _count_sources(site_data: Dict[str, Any], needle: str) -> int:
    if not needle:
        return 0
    count = 0
    sources: List[str] = []
    if needle in str(site_data.get("page_text", "")):
        sources.append("homepage")
    for item in site_data.get("js_analysis", {}).get("js_content", []) or []:
        if isinstance(item, dict) and needle in str(item.get("content", "")):
            sources.append(str(item.get("url", "js")))
    for item in site_data.get("api_analysis", {}).get("api_content", []) or []:
        if isinstance(item, dict) and needle in str(item.get("content", "")):
            sources.append(str(item.get("url", "api")))
    return len(set(sources))


def score_finding(finding: Any, site_data: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """Add confidence metadata to an existing finding without changing scanner logic."""
    site_data = site_data or {}
    score = 0
    reasons: List[str] = []

    if getattr(finding, "exploitable", False):
        score += 35
        reasons.append("scanner marked exploitable")

    severity = str(getattr(finding, "severity", "")).upper()
    if severity == "CRITICAL":
        score += 25
    elif severity == "HIGH":
        score += 18
    elif severity == "MEDIUM":
        score += 10
    elif severity == "LOW":
        score += 5

    evidence = str(getattr(finding, "evidence", ""))
    if evidence:
        score += 10
        reasons.append("has evidence string")

    strong_words = ["reflected", "assigned", "within", "near", "found", "resolved", "status="]
    if any(word in evidence.lower() for word in strong_words):
        score += 10
        reasons.append("evidence contains concrete proof wording")

    location = str(getattr(finding, "location", ""))
    if location and location not in ("Unknown", "JavaScript Code"):
        score += 8
        reasons.append("specific location/source present")

    coverage = site_data.get("coverage", {}) or {}
    if coverage.get("files_fetched") or coverage.get("routes_fetched") or coverage.get("api_responses_fetched"):
        score += 7
        reasons.append("expanded collector evidence present")

    score = max(0, min(score, 100))
    if score >= 75:
        label = "HIGH"
    elif score >= 45:
        label = "MEDIUM"
    else:
        label = "LOW"

    return {
        "score": score,
        "confidence": label,
        "reasons": reasons,
    }


def score_findings(findings: Iterable[Any], site_data: Dict[str, Any] | None = None) -> List[Dict[str, Any]]:
    return [score_finding(f, site_data) for f in findings]
