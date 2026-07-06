from modules.judge_review_mode import build_judge_review_report, evidence_record, stable_hash


def test_stable_hash_is_deterministic():
    assert stable_hash({"b": 2, "a": 1}) == stable_hash({"a": 1, "b": 2})


def test_evidence_record_includes_integrity_metadata():
    record = evidence_record("source", "type", "secret=<redacted>", {"severity": "HIGH"})
    data = record.to_dict()
    assert data["source"] == "source"
    assert len(data["sha256"]) == 64
    assert data["byte_length"] > 0
    assert data["metadata"]["severity"] == "HIGH"


def test_build_judge_review_report_summarizes_sections():
    result = {
        "target": "https://example.com",
        "findings": [{
            "type": "EXPOSED_CONFIG",
            "location": "https://example.com/.env",
            "evidence": "API_KEY=<redacted>",
            "severity": "CRITICAL",
            "confidence": 94,
            "false_positive_risk": "LOW",
            "attacker_value": "API abuse risk",
        }],
        "gear3": {"attack_paths": [{"title": "Sensitive backend exposure path", "severity": "HIGH", "confidence": 90}]},
        "lab_mode": {"payload_catalog": [{"family": "xss_reflection"}], "probes": [{"family": "xss_reflection", "url": "https://example.com?q=x", "parameter": "q", "risk": "low", "intent": "reflection"}]},
        "data_exposure": {"findings": [{"type": "DATABASE_URL", "location": "app.js", "evidence": "DATABASE_URL=<redacted>", "category": "secret_exposure", "severity": "CRITICAL", "confidence": 95}]},
    }
    report = build_judge_review_report(result)
    assert report["mode"] == "judge_review_mode"
    assert report["summary"]["evidence_records"] >= 4
    assert report["payload_catalog"]
    assert "redaction_policy" in report
