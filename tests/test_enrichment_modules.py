from modules.finding_confidence import score_finding
from modules.web3_api_mapper import classify_api_url, map_apis
from modules.web3_js_unpacker import unpack_js_text, enrich_site_data_with_unpacked_js
from modules.solana_intel import label_program_id, enrich_solana_intel


class FakeFinding:
    type = "HIGH_SLIPPAGE_EXPLOIT"
    severity = "LOW"
    location = "fixture.js"
    evidence = "Raw slippage value 15 resolved to 15%"
    exploitable = True


def test_confidence_scoring_returns_label_and_score():
    result = score_finding(FakeFinding(), {"coverage": {"files_fetched": 1}})
    assert result["confidence"] in {"LOW", "MEDIUM", "HIGH"}
    assert 0 <= result["score"] <= 100
    assert result["reasons"]


def test_api_mapper_classifies_swap_and_auth():
    assert "swap" in classify_api_url("https://x.test/api/swap/quote")["kinds"]
    assert "auth" in classify_api_url("https://x.test/api/auth/session")["kinds"]


def test_map_apis_summarizes_kinds():
    mapped = map_apis({"api_analysis": {"api_urls": ["https://x.test/api/swap", "https://x.test/api/auth"]}})
    assert mapped["total"] == 2
    assert mapped["by_kind"]["swap"] == 1
    assert mapped["by_kind"]["auth"] == 1


def test_js_unpacker_extracts_routes_env_and_base64():
    unpacked = unpack_js_text("const r='/api/swap'; const e='NEXT_PUBLIC_RPC_URL'; const b='L2FwaS9oaWRkZW4=';")
    assert "/api/swap" in unpacked["routes"]
    assert "NEXT_PUBLIC_RPC_URL" in unpacked["env_names"]
    assert any("/api/hidden" in item for item in unpacked["decoded_strings"])


def test_enrich_site_data_with_unpacked_js_adds_extra_items():
    data = {"js_analysis": {"js_content": [{"url": "bundle.js", "content": "const b='L2FwaS9oaWRkZW4=';"}]}}
    enriched = enrich_site_data_with_unpacked_js(data)
    assert enriched["unpacked_js"]["items_added"] == 1
    assert any(str(item.get("url", "")).startswith("unpacked::") for item in enriched["js_analysis"]["js_content"])


def test_solana_intel_labels_known_programs():
    known = label_program_id("JUP6LkbZbjS1jKKwapdHNy74zcZ3tLUZoi5QNyVTaV4")
    assert known["known"] == "true"
    assert "Jupiter" in known["label"]


def test_enrich_solana_intel_adds_known_and_unknown_lists():
    data = {"js_analysis": {"program_ids": ["JUP6LkbZbjS1jKKwapdHNy74zcZ3tLUZoi5QNyVTaV4", "Fake111111111111111111111111111111111111"]}}
    enriched = enrich_solana_intel(data)
    assert enriched["solana_intel"]["known_programs"]
    assert enriched["solana_intel"]["unknown_candidates"]
