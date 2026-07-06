from modules.redteam_lab_mode import (
    SAFE_PAYLOAD_MARKER,
    build_lab_mode_report,
    build_lab_probes,
    evaluate_probe_response,
    replace_param,
)


def test_replace_param_preserves_other_params():
    url = replace_param("https://example.com/search?q=test&page=1", "q", "FOX")
    assert "q=FOX" in url
    assert "page=1" in url


def test_build_lab_probes_detects_multiple_families():
    probes = build_lab_probes([
        "https://example.com/search?q=test",
        "https://example.com/api/users?id=123",
        "https://example.com/redirect?next=/app",
        "https://example.com/fetch?url=https://site.test",
    ])
    families = {p.family for p in probes}
    assert "xss_reflection" in families
    assert "sqli_error_probe" in families
    assert "open_redirect_probe" in families or "ssrf_url_probe" in families
    assert all(SAFE_PAYLOAD_MARKER in p.payload_preview for p in probes)


def test_evaluate_probe_response_reflection():
    probe = build_lab_probes(["https://example.com/search?q=test"])[0]
    result = evaluate_probe_response(probe, 200, "hello", 200, f"hello {probe.marker}")
    assert result.status == "reflection_confirmed"
    assert result.confidence >= 60
    assert result.exploitability["execution_attempted"] is False


def test_evaluate_probe_response_sql_error_hint():
    probe = [p for p in build_lab_probes(["https://example.com/api/users?id=123"]) if p.family == "sqli_error_probe"][0]
    result = evaluate_probe_response(probe, 200, "ok", 500, "SQL syntax error near FOX")
    assert result.status == "error_behavior_confirmed"
    assert result.confidence >= 55


def test_build_lab_mode_report():
    report = build_lab_mode_report(["https://example.com/search?q=test", "https://example.com/api/users?id=123"])
    assert report["summary"]["probe_count"] >= 2
    assert report["payload_catalog"]
    assert report["probes"]
