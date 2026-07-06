from modules.fox_site_intelligence import (
    AuthContext,
    FoxSiteIntelligence,
    body_hash,
    normalize_url,
    redacted,
    summarize_findings,
)


def test_normalize_url_requires_http_and_skips_static():
    assert normalize_url("/api/test") is None
    assert normalize_url("/api/test", base="https://example.com") == "https://example.com/api/test"
    assert normalize_url("https://example.com/logo.png") is None


def test_redacted_masks_sensitive_assignment():
    text = "api_key=super_secret_fixture_value password=another_fixture_secret"
    out = redacted(text)
    assert "super_secret_fixture_value" not in out
    assert "another_fixture_secret" not in out
    assert "redacted" in out


def test_extract_routes_detects_admin_and_graphql_candidates():
    scanner = FoxSiteIntelligence("https://example.com")
    blob = "'/api/admin/users' '/graphql' query AdminUsers { users { id } } window.solana isPhantom"
    scanner.extract_routes_from_blob("https://example.com/app.js", blob)
    scanner.extract_from_text("https://example.com", blob)
    assert any("/api/admin/users" in u for u in scanner.sitemap.admin_candidates)
    assert any("graphql" in u for u in scanner.sitemap.graphql_candidates)
    assert "window.solana" in scanner.sitemap.web3_markers


def test_add_finding_includes_attacker_value():
    scanner = FoxSiteIntelligence("https://example.com")
    scanner.add_finding("PUBLIC_ADMIN_ENDPOINT", "HIGH", "x", "/admin", "HTTP 200", 88, "admin risk", "fix")
    finding = scanner.findings[0]
    assert finding.attacker_value
    assert finding.confidence == 88


def test_summarize_findings_counts_severity():
    scanner = FoxSiteIntelligence("https://example.com")
    scanner.add_finding("A", "CRITICAL", "a", "/", "proof", 90, "impact", "fix")
    scanner.add_finding("B", "LOW", "b", "/", "proof", 40, "impact", "fix")
    summary = summarize_findings(scanner.findings)
    assert summary["total"] == 2
    assert summary["counts"]["CRITICAL"] == 1
    assert summary["high_confidence"] == 1


def test_auth_context_from_empty_files_not_required():
    ctx = AuthContext(name="public")
    assert ctx.headers == {}
    assert ctx.cookies == {}
    assert body_hash("abc") == body_hash("abc")
