#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import re
from typing import Any, Dict, Iterable, List, Tuple

STRONG_EVIDENCE_WORDS = [
    "validated", "magic bytes", "uid=", "gid=", "root:", "instance-id",
    "vmid", "project-id", "status changed", "reflected", "downloadable",
    "exposed", "decoded", "key=value", "repositoryformatversion", "phpinfo",
]

WEAK_FINDING_TYPES = [
    "MISSING_SECURITY_HEADER", "INFORMATION_DISCLOSURE", "ROBOTS", "SITEMAP",
]

HIGH_SIGNAL_TYPES = [
    "SQLI", "SSRF", "COMMAND", "PCM_COMMAND", "PATH_TRAVERSAL", "FAM_PATH",
    "GIT_REPOSITORY", "ENV_FILE", "BACKUP_FILE", "SENSITIVE_DATA",
    "CONFIG_SECRETS", "JWT_ALGORITHM", "CORS_WILDCARD", "XXE", "IDOR",
]

SECRET_PATTERNS = [
    re.compile(r"sk_live_[A-Za-z0-9]{12,}"),
    re.compile(r"sk_test_[A-Za-z0-9]{12,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"AIza[0-9A-Za-z_\-]{20,}"),
    re.compile(r"eyJ[A-Za-z0-9_\-]{8,}\.[A-Za-z0-9_\-]{8,}\.[A-Za-z0-9_\-]{8,}"),
    re.compile(r"(?i)(password|passwd|secret|token|api[_-]?key)([\"']?\s*[:=]\s*[\"']?)([^\s\"']{10,})"),
]


def _get(obj: Any, name: str, default: Any = "") -> Any:
    if isinstance(obj, dict):
        return obj.get(name, default)
    return getattr(obj, name, default)


def _set(obj: Any, name: str, value: Any) -> None:
    if isinstance(obj, dict):
        obj[name] = value
    else:
        try:
            setattr(obj, name, value)
        except Exception:
            pass


def redact_text(value: Any) -> Any:
    if value is None:
        return value
    text = str(value)
    for pattern in SECRET_PATTERNS:
        def repl(match: re.Match) -> str:
            if len(match.groups()) == 3:
                return f"{match.group(1)}{match.group(2)}<redacted:{len(match.group(3))}>"
            token = match.group(0)
            return token[:8] + "...<redacted>..." + token[-4:]
        text = pattern.sub(repl, text)
    return text


def finding_fingerprint(finding: Any) -> str:
    raw = "|".join([
        str(_get(finding, "type", "")),
        str(_get(finding, "severity", "")),
        str(_get(finding, "location", "")),
        str(_get(finding, "payload", ""))[:120],
    ])
    return hashlib.sha1(raw.encode("utf-8", errors="ignore")).hexdigest()[:16]


def score_finding(finding: Any) -> Dict[str, Any]:
    f_type = str(_get(finding, "type", "")).upper()
    severity = str(_get(finding, "severity", "")).upper()
    location = str(_get(finding, "location", ""))
    evidence = str(_get(finding, "evidence", "") or "")
    payload = str(_get(finding, "payload", "") or "")
    exploitable = bool(_get(finding, "exploitable", False))

    score = 0
    reasons: List[str] = []
    warnings: List[str] = []

    if severity == "CRITICAL":
        score += 25
    elif severity == "HIGH":
        score += 18
    elif severity == "MEDIUM":
        score += 10
    elif severity == "LOW":
        score += 5

    if exploitable:
        score += 20
        reasons.append("marked exploitable")

    if evidence:
        score += 15
        reasons.append("evidence present")
        low_evidence = evidence.lower()
        hits = [word for word in STRONG_EVIDENCE_WORDS if word in low_evidence]
        if hits:
            score += min(20, len(hits) * 6)
            reasons.append("strong evidence markers: " + ", ".join(hits[:4]))
    else:
        warnings.append("no evidence string")

    if payload:
        score += 6
        reasons.append("payload recorded")

    if location and location.lower() not in {"unknown", "http headers"}:
        score += 8
        reasons.append("specific location")

    if any(t in f_type for t in HIGH_SIGNAL_TYPES):
        score += 12
        reasons.append("high-signal finding type")

    if any(t in f_type for t in WEAK_FINDING_TYPES):
        score -= 15
        warnings.append("weak/noisy finding class")

    if "MISSING_SECURITY_HEADER" in f_type and not exploitable:
        score = min(score, 35)
        warnings.append("security-header finding is informational unless chained")

    if "NO_RATE_LIMITING" in f_type:
        warnings.append("rate-limit result needs manual verification because status-code-only checks can be noisy")
        score = min(score, 55)

    if "CSRF" in f_type:
        warnings.append("CSRF result needs authenticated workflow proof")
        score = min(score, 60)

    if location == "/" and not evidence:
        warnings.append("root-path finding without evidence is weak")
        score = min(score, 45)

    score = max(0, min(score, 100))
    label = "HIGH" if score >= 75 else "MEDIUM" if score >= 45 else "LOW"
    return {
        "score": score,
        "confidence": label,
        "reasons": reasons,
        "warnings": warnings,
        "fingerprint": finding_fingerprint(finding),
    }


def annotate_finding(finding: Any) -> Any:
    accuracy = score_finding(finding)
    _set(finding, "accuracy", accuracy)

    # Preserve scanner logic but avoid leaking full secrets into generated reports.
    if _get(finding, "evidence", None):
        _set(finding, "evidence", redact_text(_get(finding, "evidence")))
    if _get(finding, "payload", None):
        _set(finding, "payload", redact_text(_get(finding, "payload")))
    if _get(finding, "exploit_code", None):
        _set(finding, "exploit_code", redact_text(_get(finding, "exploit_code")))
    return finding


def dedupe_findings(findings: Iterable[Any]) -> Tuple[List[Any], Dict[str, Any]]:
    seen: Dict[str, Any] = {}
    duplicates = 0
    for finding in findings:
        fp = finding_fingerprint(finding)
        if fp in seen:
            duplicates += 1
            existing = seen[fp]
            if score_finding(finding)["score"] > score_finding(existing)["score"]:
                seen[fp] = finding
            continue
        seen[fp] = finding
    return list(seen.values()), {"duplicates_removed": duplicates, "unique_findings": len(seen)}


def enhance_scan_results(scan_data: Dict[str, Any]) -> Dict[str, Any]:
    findings = scan_data.get("vulnerabilities", []) or []
    deduped, dedupe_meta = dedupe_findings(findings)
    annotated = [annotate_finding(f) for f in deduped]

    confidence_counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
    noisy = []
    for finding in annotated:
        accuracy = _get(finding, "accuracy", {}) or {}
        label = accuracy.get("confidence", "LOW")
        confidence_counts[label] = confidence_counts.get(label, 0) + 1
        if label == "LOW" or accuracy.get("warnings"):
            noisy.append({
                "type": _get(finding, "type", ""),
                "location": _get(finding, "location", ""),
                "confidence": label,
                "warnings": accuracy.get("warnings", []),
            })

    scan_data["vulnerabilities"] = annotated
    scan_data["accuracy_summary"] = {
        **dedupe_meta,
        "confidence_counts": confidence_counts,
        "needs_manual_review": noisy[:50],
    }
    return scan_data
