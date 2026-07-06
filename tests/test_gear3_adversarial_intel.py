from modules.gear3_adversarial_intel import (
    build_attack_paths,
    build_gear3_report,
    classify_response,
    extract_business_logic_risks,
    extract_graphql_attack_surface,
    extract_idor_candidates,
    extract_parameter_risks,
    extract_web3_transaction_risks,
)


def test_parameter_risk_detects_user_id_and_redirect():
    findings = extract_parameter_risks([
        "https://example.com/api/orders?user_id=123",
        "https://example.com/login?redirect=https://example.com/app",
    ])
    types = [f.type for f in findings]
    assert types.count("PARAMETER_TAMPER_RISK") == 2
    assert any("IDOR" in f.evidence for f in findings)


def test_idor_candidates_detect_object_paths():
    findings = extract_idor_candidates(["https://example.com/api/users/123/profile"])
    assert findings
    assert findings[0].type == "IDOR_BOLA_CANDIDATE"
    assert findings[0].severity == "HIGH"


def test_business_logic_detects_billing_and_refund():
    findings = extract_business_logic_risks(["https://example.com/api/billing/export"], {"app.js": "refundPayment checkout price balance"})
    assert any(f.type == "BUSINESS_LOGIC_SURFACE" for f in findings)
    assert any(f.severity == "HIGH" for f in findings)


def test_graphql_attack_surface_flags_high_risk_mutation():
    findings = extract_graphql_attack_surface({"app.js": "mutation UpdateUserRole { updateUserRole(id: 1) { id } }"})
    assert findings
    assert findings[0].severity == "HIGH"


def test_web3_transaction_risk_detects_signing_flow():
    findings = extract_web3_transaction_risks({"app.js": "wallet.signTransaction(tx); const slippage = 99; recipient = to"})
    assert findings
    assert findings[0].type == "WEB3_TRANSACTION_RISK_SURFACE"


def test_response_classifier_labels_sensitive_json():
    result = classify_response(200, '{"email":"a@example.com","role":"admin"}', "application/json")
    assert "reachable" in result["labels"]
    assert "sensitive_fields" in result["labels"]


def test_attack_paths_from_base_admin_finding():
    paths = build_attack_paths([], base_findings=[{
        "type": "BROKEN_ADMIN_ACCESS_CONTROL",
        "severity": "CRITICAL",
        "confidence": 96,
        "evidence": "public=403,user=200",
        "location": "https://example.com/api/admin/users",
    }])
    assert paths
    assert paths[0].severity == "CRITICAL"


def test_build_gear3_report_combines_findings():
    report = build_gear3_report(
        {"endpoints": ["https://example.com/api/users/123?user_id=456", "https://example.com/api/billing/export"], "admin_candidates": [], "graphql_candidates": []},
        findings=[],
        access_matrix=[{"url": "https://example.com/api/users/123", "public": 403, "user": 200}],
        blobs={"app.js": "mutation DeleteUser { deleteUser(id: 1) { id } } signTransaction slippage"},
    )
    assert report["summary"]["total_gear3_findings"] >= 3
    assert "findings" in report
    assert "attack_paths" in report
