#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import re
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, Iterable, List, Optional
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

SAFE_PAYLOAD_MARKER = "FOX_LAB_PROOF"

PAYLOAD_CATALOG = [
    {
        "family": "xss_reflection",
        "intent": "reflection/context proof",
        "payload": f"{SAFE_PAYLOAD_MARKER}_XSS_{{id}}",
        "risk": "low",
        "description": "Benign marker used to prove reflection and response context without script execution.",
    },
    {
        "family": "sqli_error_probe",
        "intent": "parser/error proof",
        "payload": f"{SAFE_PAYLOAD_MARKER}_SQL'",
        "risk": "low",
        "description": "Benign quote-suffixed marker used to detect SQL parser/error behavior without extracting data.",
    },
    {
        "family": "cmdi_marker_probe",
        "intent": "command-injection surface classification",
        "payload": f"{SAFE_PAYLOAD_MARKER}_CMD",
        "risk": "low",
        "description": "Benign marker used to classify command-like parameters; does not execute shell metacharacters.",
    },
    {
        "family": "ssrf_url_probe",
        "intent": "URL-fetch parameter classification",
        "payload": f"https://example.invalid/{SAFE_PAYLOAD_MARKER}_SSRF_{{id}}",
        "risk": "low",
        "description": "Non-routable proof URL marker for identifying SSRF-like input handling without callback collection.",
    },
    {
        "family": "open_redirect_probe",
        "intent": "redirect behavior proof",
        "payload": f"https://example.invalid/{SAFE_PAYLOAD_MARKER}_REDIR_{{id}}",
        "risk": "low",
        "description": "Benign external URL marker used to detect redirect parameter behavior.",
    },
]

PARAM_FAMILIES = {
    "xss_reflection": {"q", "query", "search", "s", "keyword", "name", "message", "comment", "title", "next", "return", "returnurl"},
    "sqli_error_probe": {"id", "user", "userid", "user_id", "account", "account_id", "order", "order_id", "invoice", "invoice_id", "product", "item"},
    "ssrf_url_probe": {"url", "uri", "link", "target", "next", "callback", "webhook", "image", "avatar", "redirect_uri"},
    "open_redirect_probe": {"redirect", "redirect_uri", "return", "returnurl", "next", "continue", "callback"},
    "cmdi_marker_probe": {"host", "domain", "ip", "cmd", "command", "ping", "lookup", "path", "file"},
}

ERROR_HINTS = {
    "sqli_error_probe": re.compile(r"SQL syntax|SQLSTATE|PostgreSQL|MySQL|MariaDB|ORA-|SQLite|syntax error", re.I),
    "cmdi_marker_probe": re.compile(r"sh:|bash:|cmd.exe|PowerShell|spawn|exec|child_process|command not found", re.I),
    "ssrf_url_probe": re.compile(r"ECONNREFUSED|ENOTFOUND|EAI_AGAIN|connection refused|invalid host|fetch failed", re.I),
}


@dataclass
class LabProbe:
    family: str
    url: str
    parameter: str
    marker: str
    payload_preview: str
    intent: str
    risk: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class LabResult:
    family: str
    url: str
    parameter: str
    status: str
    confidence: int
    evidence: str
    exploitability: Dict[str, Any]
    safe_next_steps: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def fingerprint(value: str) -> str:
    return hashlib.sha1(value.encode("utf-8", errors="ignore")).hexdigest()[:10]


def normalize_param(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (value or "").lower())


def payload_for_family(family: str, marker_id: str) -> str:
    for item in PAYLOAD_CATALOG:
        if item["family"] == family:
            return item["payload"].format(id=marker_id)
    return f"{SAFE_PAYLOAD_MARKER}_{marker_id}"


def replace_param(url: str, param: str, value: str) -> str:
    parsed = urlparse(url)
    pairs = parse_qsl(parsed.query, keep_blank_values=True)
    updated = [(k, value if k == param else v) for k, v in pairs]
    return urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, urlencode(updated, doseq=True), parsed.fragment))


def build_lab_probes(urls: Iterable[str], limit: int = 200) -> List[LabProbe]:
    probes: List[LabProbe] = []
    seen = set()
    for url in urls:
        parsed = urlparse(url)
        if not parsed.query:
            continue
        params = parse_qsl(parsed.query, keep_blank_values=True)
        for param, _ in params:
            norm = normalize_param(param)
            for family, names in PARAM_FAMILIES.items():
                if norm in {normalize_param(x) for x in names}:
                    marker = f"{SAFE_PAYLOAD_MARKER}_{fingerprint(url + param + family)}"
                    payload = payload_for_family(family, marker)
                    proof_url = replace_param(url, param, payload)
                    key = f"{family}:{param}:{parsed.path}"
                    if key in seen:
                        continue
                    seen.add(key)
                    meta = next((p for p in PAYLOAD_CATALOG if p["family"] == family), {})
                    probes.append(LabProbe(family, proof_url, param, marker, payload[:140], meta.get("intent", "proof"), meta.get("risk", "low")))
                    if len(probes) >= limit:
                        return probes
    return probes


def evaluate_probe_response(probe: LabProbe, baseline_status: int, baseline_body: str, test_status: int, test_body: str, headers: Optional[Dict[str, str]] = None) -> LabResult:
    headers = headers or {}
    low = (test_body or "").lower()
    reflected = probe.marker.lower() in low or probe.payload_preview.lower() in low
    changed_status = baseline_status != test_status
    changed_length = abs(len(test_body or "") - len(baseline_body or "")) > max(80, int(len(baseline_body or "") * 0.15))
    error_hint = bool(ERROR_HINTS.get(probe.family, re.compile(r"a^", re.I)).search(test_body or ""))
    location_header = headers.get("location", "") or headers.get("Location", "")
    redirected_to_marker = probe.family == "open_redirect_probe" and SAFE_PAYLOAD_MARKER.lower() in location_header.lower()

    confidence = 25
    labels: List[str] = []
    if reflected:
        labels.append("marker_reflected")
        confidence += 35
    if error_hint:
        labels.append("family_error_hint")
        confidence += 30
    if changed_status:
        labels.append("status_changed")
        confidence += 10
    if changed_length:
        labels.append("body_shape_changed")
        confidence += 10
    if redirected_to_marker:
        labels.append("redirect_marker_in_location")
        confidence += 40
    confidence = min(confidence, 95)

    if redirected_to_marker:
        status = "redirect_behavior_confirmed"
    elif reflected:
        status = "reflection_confirmed"
    elif error_hint:
        status = "error_behavior_confirmed"
    elif changed_status or changed_length:
        status = "behavior_changed_needs_review"
    else:
        status = "no_signal"

    return LabResult(
        family=probe.family,
        url=probe.url,
        parameter=probe.parameter,
        status=status,
        confidence=confidence,
        evidence=", ".join(labels) or "No probe-specific response signal observed.",
        exploitability={
            "execution_attempted": False,
            "destructive_action": False,
            "payload_intent": probe.intent,
            "risk_level": probe.risk,
            "baseline_status": baseline_status,
            "test_status": test_status,
        },
        safe_next_steps=next_steps_for_family(probe.family, status),
    )


def next_steps_for_family(family: str, status: str) -> List[str]:
    if status == "no_signal":
        return ["Keep as low priority unless other evidence supports it."]
    mapping = {
        "xss_reflection": ["Inspect reflection context", "Check escaping/encoding", "Validate in a dedicated lab browser manually"],
        "sqli_error_probe": ["Compare baseline vs marker response", "Confirm DB-specific errors only in lab", "Do not extract data"],
        "cmdi_marker_probe": ["Review backend command execution paths", "Confirm with harmless lab-only canary if rules allow", "Do not run OS commands"],
        "ssrf_url_probe": ["Check server fetch behavior", "Use owned lab canary only if explicitly allowed", "Do not target metadata services"],
        "open_redirect_probe": ["Check Location header", "Verify allowlist and OAuth redirect validation", "Avoid phishing-style payloads"],
    }
    return mapping.get(family, ["Manually verify in lab scope."])


def build_lab_mode_report(urls: Iterable[str], max_probes: int = 200) -> Dict[str, Any]:
    probes = build_lab_probes(urls, limit=max_probes)
    return {
        "summary": {
            "payload_families": sorted({p.family for p in probes}),
            "probe_count": len(probes),
            "execution_model": "proof-only; no destructive actions; no credential extraction",
        },
        "payload_catalog": PAYLOAD_CATALOG,
        "probes": [p.to_dict() for p in probes],
    }
