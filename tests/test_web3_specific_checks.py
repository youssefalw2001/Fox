import pytest

from modules.web3_specific_checks import Web3SpecificChecks


def site_data(*chunks):
    return {
        "page_text": chunks[0] if chunks else "",
        "page_status": 200,
        "js_analysis": {
            "program_ids": [],
            "rpc_urls": [],
            "js_content": [
                {"url": f"fixture-{i}.js", "content": chunk}
                for i, chunk in enumerate(chunks[1:], start=1)
            ],
        },
        "api_analysis": {"api_urls": [], "api_content": []},
        "routes": [],
    }


def test_unlimited_approval_requires_nearby_context():
    checker = Web3SpecificChecks()
    positive = site_data(
        "",
        "function approveFlow(){ return createApproveInstruction(owner, spender, MAX_U64); }",
    )
    negative = site_data(
        "",
        "const MAX_U64 = '18446744073709551615';\n" + ("x" * 600) + "\nfunction approve(){}",
    )

    assert checker.check_unlimited_approvals("https://example.test", positive)
    assert checker.check_unlimited_approvals("https://example.test", negative) == []


def test_high_slippage_handles_bps_vs_percent():
    checker = Web3SpecificChecks()
    fifty_bps = site_data("", "const swapConfig = { slippageBps: 50, mode: 'swap' };")
    high_percent = site_data("", "const swapConfig = { slippage: 15, mode: 'swap' };")

    assert checker.check_high_slippage("https://example.test", fifty_bps) == []
    findings = checker.check_high_slippage("https://example.test", high_percent)
    assert findings
    assert findings[0].type == "HIGH_SLIPPAGE_EXPLOIT"


def test_unencrypted_websocket_finds_rpc_context_only():
    checker = Web3SpecificChecks()
    unrelated = site_data("", "const chat = 'ws://chat.example.test/socket';")
    related = site_data("", "const rpc = 'ws://solana-rpc.example.test/socket';")

    assert checker.check_unencrypted_websocket("https://example.test", unrelated) == []
    findings = checker.check_unencrypted_websocket("https://example.test", related)
    assert findings
    assert findings[0].type == "UNENCRYPTED_WEBSOCKET_RPC"


def test_signature_replay_does_not_fire_when_blockhash_present():
    checker = Web3SpecificChecks()
    protected = site_data("", "await wallet.signTransaction(tx); tx.recentBlockhash = hash;")
    missing = site_data("", "await wallet.signTransaction(tx); send(tx);")

    assert checker.check_signature_replay("https://example.test", protected) == []
    findings = checker.check_signature_replay("https://example.test", missing)
    assert findings
    assert findings[0].type == "SIGNATURE_REPLAY_VULNERABLE"


def test_privy_placeholder_secret_is_ignored_but_real_value_is_flagged():
    checker = Web3SpecificChecks()
    placeholder = site_data("", "const PRIVY_CLIENT_SECRET = 'changeme'; const privy = true;")
    realish = site_data("", "const PRIVY_CLIENT_SECRET = 'sk_live_competition_fixture_123456'; const privy = true;")

    assert checker.check_privy_jwt_bypass("https://example.test", placeholder) == []
    findings = checker.check_privy_jwt_bypass("https://example.test", realish)
    assert findings
    assert findings[0].type == "PRIVY_SECRET_EXPOSED"


def test_master_runner_uses_supplied_site_data_without_network_collection(monkeypatch):
    checker = Web3SpecificChecks()

    def fail_collect(_target):
        raise AssertionError("collect_site_data should not be called when site_data is supplied")

    monkeypatch.setattr(checker, "collect_site_data", fail_collect)
    data = site_data("", "const swapConfig = { slippage: 25, mode: 'swap' };")
    findings = checker.run_real_exploit_scan("https://example.test", data)
    assert any(f.type == "HIGH_SLIPPAGE_EXPLOIT" for f in findings)
