from modules.data_exposure_intel import (
    build_data_exposure_report,
    extract_graphql_summary,
    extract_openapi_summary,
    extract_source_map_summary,
    redact_secret,
    scan_text_for_exposures,
)


def test_redact_secret_masks_backend_values():
    text = "JWT_SECRET=fixture_secret_value_1234567890"
    redacted = redact_secret(text)
    assert "fixture_secret_value_1234567890" not in redacted
    assert "redacted" in redacted


def test_detects_private_key_and_database_url():
    text = "-----BEGIN PRIVATE KEY-----\nabc\n-----END PRIVATE KEY-----\nDATABASE_URL=postgres://user:pass@example.com/db"
    findings = scan_text_for_exposures("https://example.com/.env", text, "text/plain")
    types = {f.type for f in findings}
    assert "PRIVATE_KEY_BLOCK" in types
    assert "DATABASE_URL" in types
    assert all("pass@example" not in f.evidence for f in findings)


def test_detects_storage_and_sensitive_filename():
    text = "https://bucket.s3.amazonaws.com/backup-2025-users.sql"
    findings = scan_text_for_exposures("https://example.com/app.js", text)
    storage = [f for f in findings if f.category == "storage_reference"]
    assert storage
    assert storage[0].severity == "HIGH"


def test_openapi_summary_extracts_admin_paths():
    spec = '{"openapi":"3.0.0","paths":{"/api/admin/users":{"get":{}},"/api/billing/export":{"post":{}}}}'
    summary = extract_openapi_summary("openapi.json", spec)
    assert summary["valid_json"] is True
    assert "/api/admin/users" in summary["admin_paths"]
    assert any("billing" in op.lower() for op in summary["dangerous_ops"])


def test_source_map_summary_extracts_interesting_sources_and_comments():
    smap = '{"version":3,"sources":["src/admin/auth.ts"],"sourcesContent":["// TODO disable debug auth before prod"]}'
    summary = extract_source_map_summary("app.js.map", smap)
    assert summary["valid_json"] is True
    assert summary["interesting_sources"]
    assert summary["comments"]


def test_graphql_summary_extracts_operations():
    summary = extract_graphql_summary("app.js", "mutation UpdateUserRole { updateUserRole(id: 1) { id } }")
    assert "mutation UpdateUserRole" in summary["operations"]
    assert "updateUserRole" in summary["interesting_fields"]


def test_build_report_combines_findings():
    report = build_data_exposure_report({"app.js": "const x='AIzaAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA'; query Users { user { id } }"})
    assert report["summary"]["total_findings"] >= 1
    assert "findings" in report
