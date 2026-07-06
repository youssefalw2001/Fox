from modules.phantom_dapp_catalog import (
    blocked_brand,
    domain_of,
    extract_urls,
    normalize_url,
    rank_dapps,
    score_dapp,
)


def test_normalize_url_adds_https_and_skips_static_assets():
    assert normalize_url("example.xyz") == "https://example.xyz"
    assert normalize_url("https://example.xyz/logo.png") is None


def test_domain_of_removes_www():
    assert domain_of("https://www.example.xyz/app") == "example.xyz"


def test_extract_urls_handles_href_and_absolute_urls():
    html = '<a href="/app">App</a> https://demo.xyz/play'
    urls = extract_urls(html, base_url="https://example.xyz")
    assert "https://example.xyz/app" in urls
    assert "https://demo.xyz/play" in urls


def test_blocked_brand_catches_large_brands():
    assert blocked_brand("jupiter.exchange") == "jupiter"
    assert blocked_brand("small-defi.xyz") is None


def test_score_dapp_uses_markers_with_monkeypatched_fetch(monkeypatch):
    def fake_collect(url, timeout=8, max_scripts=8):
        return "window.solana isPhantom connect wallet mainnet-beta staking vault"

    monkeypatch.setattr("modules.phantom_dapp_catalog.collect_homepage_and_scripts", fake_collect)
    result = score_dapp("https://tiny-vault.xyz", seen={})
    assert result.score >= 70
    assert result.fresh is True
    assert result.verdict in {"EXCELLENT_PHANTOM_DAPP", "GOOD_PHANTOM_DAPP"}


def test_rank_dapps_filters_seen_domains(monkeypatch, tmp_path):
    def fake_collect(url, timeout=8, max_scripts=8):
        return "window.solana isPhantom connect wallet mainnet-beta"

    monkeypatch.setattr("modules.phantom_dapp_catalog.collect_homepage_and_scripts", fake_collect)
    seen = tmp_path / "seen.json"
    first = rank_dapps(["https://fresh-one.xyz"], seen_path=str(seen), min_score=1)
    second = rank_dapps(["https://fresh-one.xyz"], seen_path=str(seen), min_score=1)
    assert len(first) == 1
    assert second == []
