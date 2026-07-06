from modules.mega_accuracy_enhancer import (
    dedupe_findings,
    enhance_scan_results,
    redact_text,
    score_finding,
)


class Finding:
    def __init__(self, type="SQLI_ERROR_BASED", severity="CRITICAL", location="/api/user?id=", payload="'", evidence="validated sql error", exploitable=True):
        self.type = type
        self.severity = severity
        self.location = location
        self.payload = payload
        self.evidence = evidence
        self.description = "fixture"
        self.remediation = "fix"
        self.exploitable = exploitable
        self.exploit_code = None


def test_redact_text_masks_generic_secret_assignment():
    text = "password=super_long_fixture_password_123 token=fixture_token_value_12345"
    redacted = redact_text(text)
    assert "super_long_fixture_password_123" not in redacted
    assert "fixture_token_value_12345" not in redacted
    assert "redacted" in redacted


def test_score_finding_high_for_strong_validated_evidence():
    finding = Finding(evidence="validated magic bytes root: uid= gid= exposed")
    scored = score_finding(finding)
    assert scored["confidence"] == "HIGH"
    assert scored["score"] >= 75
    assert scored["fingerprint"]


def test_score_finding_marks_weak_security_header_as_low_or_medium():
    finding = Finding(
        type="MISSING_SECURITY_HEADER",
        severity="LOW",
        location="HTTP Headers",
        payload=None,
        evidence=None,
        exploitable=False,
    )
    scored = score_finding(finding)
    assert scored["score"] <= 35
    assert scored["warnings"]


def test_dedupe_findings_removes_duplicate_fingerprint():
    one = Finding()
    two = Finding()
    deduped, meta = dedupe_findings([one, two])
    assert len(deduped) == 1
    assert meta["duplicates_removed"] == 1


def test_enhance_scan_results_adds_accuracy_summary_and_annotations():
    data = {"vulnerabilities": [Finding(), Finding(type="MISSING_SECURITY_HEADER", severity="LOW", location="HTTP Headers", evidence=None, exploitable=False)]}
    enhanced = enhance_scan_results(data)
    assert "accuracy_summary" in enhanced
    assert enhanced["accuracy_summary"]["unique_findings"] == 2
    assert all(hasattr(v, "accuracy") for v in enhanced["vulnerabilities"])
