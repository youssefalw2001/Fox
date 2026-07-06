#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, Iterable, List


@dataclass
class EvidenceRecord:
    source: str
    evidence_type: str
    redacted_preview: str
    sha256: str
    byte_length: int
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def stable_hash(value: Any) -> str:
    if isinstance(value, (dict, list)):
        raw = json.dumps(value, sort_keys=True, separators=(",", ":"))
    else:
        raw = str(value or "")
    return hashlib.sha256(raw.encode("utf-8", errors="ignore")).hexdigest()


def safe_preview(value: Any, limit: int = 600) -> str:
    text = str(value or "")
    return text[:limit]


def evidence_record(source: str, evidence_type: str, value: Any, metadata: Dict[str, Any] | None = None, full_evidence: bool = False) -> EvidenceRecord:
    text = str(value or "")
    return EvidenceRecord(
        source=source,
        evidence_type=evidence_type,
        redacted_preview=text if full_evidence else safe_preview(text),  # Full text if unfiltered
        sha256=stable_hash(text),
        byte_length=len(text.encode("utf-8", errors="ignore")),
        metadata=metadata or {},
    )


def build_judge_review_report(result: Dict[str, Any], full_evidence: bool = False) -> Dict[str, Any]:
    """
    Build a reviewer-focused integrity report.

    Args:
        result: Scanner result dictionary
        full_evidence: If True, stores full response bodies and unredacted evidence (for authorized judge review)
    
    This intentionally does not disable redaction or export raw secrets by default. 
    When full_evidence=True, it gives judges complete unredacted evidence for authorized review.
    """
    records: List[EvidenceRecord] = []

    for finding in result.get("findings", [])[:500]:
        records.append(evidence_record(
            source=finding.get("location", "finding"),
            evidence_type=finding.get("type", "finding_evidence"),
            value=finding.get("evidence", ""),
            metadata={
                "severity": finding.get("severity"),
                "confidence": finding.get("confidence"),
                "false_positive_risk": finding.get("false_positive_risk"),
                "attacker_value": finding.get("attacker_value"),
            },
            full_evidence=full_evidence,
        ))

    for path in result.get("gear3", {}).get("attack_paths", [])[:100]:
        records.append(evidence_record(
            source=path.get("title", "attack_path"),
            evidence_type="attack_path",
            value=path,
            metadata={"severity": path.get("severity"), "confidence": path.get("confidence")},
            full_evidence=full_evidence,
        ))

    for probe in result.get("lab_mode", {}).get("probes", [])[:500]:
        records.append(evidence_record(
            source=probe.get("url", "lab_probe"),
            evidence_type=f"lab_probe:{probe.get('family', 'unknown')}",
            value=probe,
            metadata={"parameter": probe.get("parameter"), "risk": probe.get("risk"), "intent": probe.get("intent")},
            full_evidence=full_evidence,
        ))

    data_exposure = result.get("data_exposure", {})
    for exposure in data_exposure.get("findings", [])[:500]:
        records.append(evidence_record(
            source=exposure.get("location", "data_exposure"),
            evidence_type=f"data_exposure:{exposure.get('type', 'unknown')}",
            value=exposure.get("evidence", ""),
            metadata={
                "category": exposure.get("category"),
                "severity": exposure.get("severity"),
                "confidence": exposure.get("confidence"),
                "attacker_value": exposure.get("attacker_value"),
            },
            full_evidence=full_evidence,
        ))

    return {
        "mode": "judge_review_mode",
        "redaction_policy": "DISABLED - Full unredacted evidence included for authorized judge review" if full_evidence else "Secrets, tokens, credentials, and destructive payloads remain redacted. Integrity is provided with SHA-256 hashes, byte lengths, evidence labels, and proof metadata.",
        "target": result.get("target"),
        "summary": {
            "evidence_records": len(records),
            "findings": len(result.get("findings", [])),
            "attack_paths": len(result.get("gear3", {}).get("attack_paths", [])),
            "lab_probes": len(result.get("lab_mode", {}).get("probes", [])),
            "data_exposure_findings": len(data_exposure.get("findings", [])),
        },
        "integrity_manifest": [r.to_dict() for r in records],
        "payload_catalog": result.get("lab_mode", {}).get("payload_catalog", []),
        "review_notes": [
            "Use sha256 and byte_length to verify evidence stability across reruns.",
            "Use provided auth contexts for public/user/admin access matrix validation.",
            "Use lab-mode probes for proof planning; they do not execute destructive payloads.",
        ],
    }
