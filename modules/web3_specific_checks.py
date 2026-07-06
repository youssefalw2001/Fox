#!/usr/bin/env python3
"""
💀🔥 REAL WEB3 EXPLOITS - FOX'S MONEY MAKER EDITION 🔥💀

Competition scanner patch:
- keeps the same 10 Web3 check categories
- adds real JS bundle collection
- removes dead/unreachable code
- reduces false positives by requiring local evidence context
- stops silent failures when debug=True
"""

from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass
from html import unescape
from typing import Dict, Iterable, List, Optional, Tuple
from urllib.parse import parse_qsl, quote, urlencode, urljoin, urlparse, urlunparse

import requests

try:
    import base58  # type: ignore
except Exception:  # dependency may be missing in competition images
    base58 = None


BASE58_RE = r"[1-9A-HJ-NP-Za-km-z]"
SOLANA_ADDRESS_RE = re.compile(rf"\b{BASE58_RE}{{32,44}}\b")
SOLANA_SECRET_RE = re.compile(rf"\b{BASE58_RE}{{87,88}}\b")
RPC_URL_RE = re.compile(r"https?://[^\"'\s<>]+|wss?://[^\"'\s<>]+", re.I)
SCRIPT_SRC_RE = re.compile(r"<script[^>]+src=[\"']([^\"']+)[\"']", re.I)
SOURCE_MAP_RE = re.compile(r"//#\s*sourceMappingURL=([^\s]+)", re.I)
ASSIGNMENT_RE = r"[\w.$\[\]'\"]+\s*[:=]\s*"


@dataclass
class Web3Vulnerability:
    """Web3-specific vulnerability finding"""
    type: str
    severity: str
    location: str
    description: str
    evidence: str
    remediation: str
    exploitable: bool
    potential_value: str = "Unknown"
    web3_specific: bool = True


class Web3SpecificChecks:
    """REAL Web3/Solana exploit detection - competition-hardened."""

    def __init__(self, timeout: int = 10, debug: bool = False, max_js_files: int = 30):
        self.timeout = timeout
        self.debug = debug
        self.max_js_files = max_js_files
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (compatible; FoxScanner/2.0; +competition)"
        })

        self.KNOWN_PROGRAMS = {
            "675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8": "Raydium AMM v4",
            "JUP6LkbZbjS1jKKwapdHNy74zcZ3tLUZoi5QNyVTaV4": "Jupiter Aggregator v6",
            "whirLbMiicVdio4qvUfM5KAg6Ct8VwpYzGff3uctyCc": "Orca Whirlpool",
            "So11111111111111111111111111111111111111112": "Wrapped SOL",
        }

        # Inert proof markers: same XSS logic, no wallet calls, no exfiltration.
        self.WALLET_XSS_PAYLOADS = [
            "<script>fox_xss_probe_1337()</script>",
            "\"><img src=x onerror=\"fox_xss_probe_1337()\">",
            "'><svg onload=\"fox_xss_probe_1337()\">",
        ]

    # ───────────────────────────── helpers ─────────────────────────────

    def _debug(self, msg: str) -> None:
        if self.debug:
            print(f"    [debug] {msg}")

    def _fetch(self, url: str, timeout: Optional[int] = None, allow_redirects: bool = True) -> Optional[requests.Response]:
        try:
            r = self.session.get(url, timeout=timeout or self.timeout, allow_redirects=allow_redirects)
            return r
        except requests.RequestException as e:
            self._debug(f"request failed {url}: {e}")
            return None

    def _safe_text(self, response: Optional[requests.Response]) -> str:
        if response is None:
            return ""
        try:
            return response.text or ""
        except Exception:
            return ""

    def _build_url(self, target: str, param: str, value: str) -> str:
        parsed = urlparse(target)
        query = dict(parse_qsl(parsed.query, keep_blank_values=True))
        query[param] = value
        return urlunparse(parsed._replace(query=urlencode(query)))

    def _get_context(self, text: str, match: str, chars: int = 160) -> str:
        try:
            idx = text.index(match)
            start = max(0, idx - chars)
            end = min(len(text), idx + len(match) + chars)
            return text[start:end]
        except ValueError:
            return ""

    def _iter_content(self, target: str, site_data: Dict) -> Iterable[Tuple[str, str]]:
        page = site_data.get("page_text")
        if page:
            yield ("homepage", page)
        else:
            r = self._fetch(target)
            yield ("homepage", self._safe_text(r))

        for item in site_data.get("js_analysis", {}).get("js_content", []):
            if isinstance(item, dict):
                yield (str(item.get("url", "js_bundle")), str(item.get("content", "")))
            else:
                yield ("js_bundle", str(item))

    def _all_content(self, target: str, site_data: Dict) -> str:
        return "\n".join(content for _, content in self._iter_content(target, site_data))

    def _is_wallet_site(self, text: str) -> bool:
        low = text.lower()
        indicators = [
            "wallet-adapter", "phantom", "solflare", "connectwallet",
            "window.solana", "signtransaction", "signmessage",
            "solana/wallet-adapter", "@solana/web3.js",
        ]
        return any(ind in low for ind in indicators)

    def _is_valid_solana_secret_key(self, key_str: str) -> bool:
        if base58 is None:
            self._debug("base58 module missing; cannot validate base58 private key candidate")
            return False
        try:
            decoded = base58.b58decode(key_str)
            # Solana secret keys are usually 64 bytes. 32-byte values are public/private scalar
            # candidates but too noisy for frontend scanning, so do not report them as secrets.
            return len(decoded) == 64
        except Exception:
            return False

    def _strong_secret_context(self, context: str) -> bool:
        low = context.lower()
        strong = [
            "secretkey", "secret_key", "privatekey", "private_key",
            "keypair.fromsecretkey", "fromsecretkey", "seedphrase",
            "mnemonic", "wallet_secret", "solana_secret",
        ]
        weak_public = ["publickey", "public_key", "programid", "program_id", "mint", "tokenaddress"]
        return any(s in low for s in strong) and not any(w in low for w in weak_public)

    def collect_site_data(self, target: str) -> Dict:
        """Fetch homepage + JS bundles and extract Web3 indicators for the 10 checks."""
        page_response = self._fetch(target)
        page_text = self._safe_text(page_response)

        js_items: List[Dict[str, str]] = []
        seen_urls = set()

        for src in SCRIPT_SRC_RE.findall(page_text):
            if len(js_items) >= self.max_js_files:
                break
            js_url = urljoin(target, src)
            if js_url in seen_urls:
                continue
            seen_urls.add(js_url)
            r_js = self._fetch(js_url, timeout=min(self.timeout, 8))
            if not r_js or r_js.status_code >= 400:
                continue
            content = self._safe_text(r_js)
            ctype = (r_js.headers.get("content-type") or "").lower()
            if ".js" not in urlparse(js_url).path and "javascript" not in ctype and len(content) > 2_000_000:
                continue

            js_items.append({"url": js_url, "content": content})

            # Pull source maps only as text hints if exposed and small enough.
            for sm in SOURCE_MAP_RE.findall(content):
                if len(js_items) >= self.max_js_files:
                    break
                sm_url = urljoin(js_url, sm.strip())
                if sm_url in seen_urls:
                    continue
                seen_urls.add(sm_url)
                r_sm = self._fetch(sm_url, timeout=min(self.timeout, 8))
                if r_sm and r_sm.status_code == 200 and len(r_sm.content) <= 2_000_000:
                    js_items.append({"url": sm_url, "content": self._safe_text(r_sm)})

        combined = page_text + "\n" + "\n".join(item["content"] for item in js_items)
        program_ids = sorted(set(SOLANA_ADDRESS_RE.findall(combined)))
        rpc_urls = sorted(set(
            u for u in RPC_URL_RE.findall(combined)
            if any(k in u.lower() for k in ("solana", "rpc", "helius", "quicknode", "alchemy", "mainnet", "devnet", "jupiter", "raydium"))
        ))

        return {
            "page_text": page_text,
            "page_status": page_response.status_code if page_response else None,
            "js_analysis": {
                "program_ids": program_ids,
                "rpc_urls": rpc_urls,
                "js_content": js_items,
                "js_urls": [item["url"] for item in js_items],
            },
        }

    # ═══════════════════════════════════════════════════════════════════
    # 💰 EXPLOIT #1: WALLET DRAINER XSS
    # ═══════════════════════════════════════════════════════════════════

    def check_wallet_drainer_xss(self, target: str, site_data: Optional[Dict] = None) -> List[Web3Vulnerability]:
        vulns: List[Web3Vulnerability] = []
        site_data = site_data or self.collect_site_data(target)
        combined = self._all_content(target, site_data)

        if not self._is_wallet_site(combined):
            return vulns

        test_params = ["search", "q", "query", "id", "token"]
        for param_name in test_params:
            for payload in self.WALLET_XSS_PAYLOADS:
                test_url = self._build_url(target, param_name, payload)
                r_test = self._fetch(test_url, timeout=5)
                body = self._safe_text(r_test)
                decoded_body = unescape(body)

                reflected_exact = payload in body or payload in decoded_body
                executable_context = (
                    "<script>fox_xss_probe_1337()</script>" in decoded_body
                    or "onerror=\"fox_xss_probe_1337()\"" in decoded_body
                    or "onload=\"fox_xss_probe_1337()\"" in decoded_body
                )

                if reflected_exact and executable_context:
                    vulns.append(Web3Vulnerability(
                        type="WALLET_DRAINER_XSS",
                        severity="CRITICAL",
                        location=f"Parameter: ?{param_name}=",
                        description="XSS on wallet-enabled site - wallet request injection path is possible",
                        evidence=f"Inert marker reflected in executable context via ?{param_name}=; status={getattr(r_test, 'status_code', 'n/a')}",
                        remediation="Encode all user input, implement CSP, and isolate wallet transaction flows from reflected input",
                        exploitable=True,
                        potential_value="50-500 SOL per victim (full wallet drain)"
                    ))
                    return vulns
        return vulns

    # ═══════════════════════════════════════════════════════════════════
    # 💰 EXPLOIT #2: PRIVATE KEY LEAKS
    # ═══════════════════════════════════════════════════════════════════

    def check_private_key_leaks(self, target: str, js_bundles: Optional[List] = None, site_data: Optional[Dict] = None) -> List[Web3Vulnerability]:
        vulns: List[Web3Vulnerability] = []
        if site_data is None:
            site_data = self.collect_site_data(target)
        if js_bundles:
            site_data.setdefault("js_analysis", {}).setdefault("js_content", []).extend(js_bundles)

        seen = set()
        for source, content in self._iter_content(target, site_data):
            for match in SOLANA_SECRET_RE.findall(content):
                if match in seen:
                    continue
                seen.add(match)
                context = self._get_context(content, match, 180)
                if self._is_valid_solana_secret_key(match) and self._strong_secret_context(context):
                    vulns.append(Web3Vulnerability(
                        type="PRIVATE_KEY_EXPOSED",
                        severity="CRITICAL",
                        location=source,
                        description="Solana secret key appears exposed in frontend code",
                        evidence=f"64-byte base58 secret key candidate near private-key context: {match[:10]}...{match[-8:]}",
                        remediation="Rotate key immediately and move signing material to secure server-side or hardware-backed storage",
                        exploitable=True,
                        potential_value="FULL WALLET ACCESS (100-10,000+ SOL)"
                    ))
        return vulns

    # ═══════════════════════════════════════════════════════════════════
    # 💰 EXPLOIT #3: UNLIMITED TOKEN APPROVALS
    # ═══════════════════════════════════════════════════════════════════

    def check_unlimited_approvals(self, target: str, site_data: Optional[Dict] = None) -> List[Web3Vulnerability]:
        vulns: List[Web3Vulnerability] = []
        site_data = site_data or self.collect_site_data(target)

        approval_patterns = ["approve", "setApprovalForAll", "increaseAllowance", "createApproveInstruction"]
        unlimited_patterns = [
            "MAX_U64", "MAX_UINT", "U64_MAX",
            "18446744073709551615", "0xFFFFFFFFFFFFFFFF", "0xffffffffffffffff",
            "Number.MAX_SAFE_INTEGER", "type(uint64).max",
        ]

        for source, content in self._iter_content(target, site_data):
            for approval in approval_patterns:
                for unlimited in unlimited_patterns:
                    regex = re.compile(rf"{re.escape(approval)}[\s\S]{{0,350}}{re.escape(unlimited)}|{re.escape(unlimited)}[\s\S]{{0,350}}{re.escape(approval)}", re.I)
                    m = regex.search(content)
                    if m:
                        vulns.append(Web3Vulnerability(
                            type="UNLIMITED_TOKEN_APPROVAL",
                            severity="HIGH",
                            location=source,
                            description="Site code contains approval logic near an unlimited amount constant",
                            evidence=f"{approval} appears within 350 chars of {unlimited}",
                            remediation="Request exact approval amounts, not unlimited allowances",
                            exploitable=True,
                            potential_value="10-100 SOL (all approved tokens)"
                        ))
                        return vulns
        return vulns

    # ═══════════════════════════════════════════════════════════════════
    # 💰 EXPLOIT #4: PROGRAM ID INJECTION
    # ═══════════════════════════════════════════════════════════════════

    def check_program_id_injection(self, target: str, program_ids: Optional[List[str]] = None, site_data: Optional[Dict] = None) -> List[Web3Vulnerability]:
        vulns: List[Web3Vulnerability] = []
        site_data = site_data or self.collect_site_data(target)
        program_ids = program_ids or site_data.get("js_analysis", {}).get("program_ids", [])
        real_programs = [pid for pid in program_ids if pid in self.KNOWN_PROGRAMS]
        if not real_programs:
            return vulns

        marker = "FoxProgramProbe111111111111111111111111111111111"
        test_params = ["program", "programId", "contract", "address", "ammId", "routeProgram"]
        for param in test_params:
            test_url = self._build_url(target, param, marker)
            r = self._fetch(test_url, timeout=5)
            body = self._safe_text(r)
            if marker not in body:
                continue
            context = self._get_context(body, marker, 250).lower()
            if any(word in context for word in ("transaction", "swap", "programid", "instruction", "route", "raydium", "jupiter")):
                vulns.append(Web3Vulnerability(
                    type="PROGRAM_ID_INJECTION",
                    severity="CRITICAL",
                    location=f"Parameter: ?{param}=",
                    description="Known Solana program flow reflects a user-controlled program identifier near transaction/swap context",
                    evidence=f"Marker reflected near transaction context; known program present: {self.KNOWN_PROGRAMS[real_programs[0]]}",
                    remediation="Hardcode/allowlist program IDs and reject user-controlled program identifiers",
                    exploitable=True,
                    potential_value="10-1,000 SOL per swap (full trade amount)"
                ))
                return vulns
        return vulns

    # ═══════════════════════════════════════════════════════════════════
    # 💰 EXPLOIT #5: UPGRADE AUTHORITY LEAKS
    # ═══════════════════════════════════════════════════════════════════

    def check_upgrade_authority_leaks(self, target: str, program_ids: Optional[List[str]] = None, site_data: Optional[Dict] = None) -> List[Web3Vulnerability]:
        vulns: List[Web3Vulnerability] = []
        site_data = site_data or self.collect_site_data(target)

        authority_terms = ["upgradeAuthority", "programAuthority", "upgrade_authority", "UPGRADE_AUTHORITY"]
        for source, content in self._iter_content(target, site_data):
            low = content.lower()
            if not any(term.lower() in low for term in authority_terms):
                continue

            for secret in SOLANA_SECRET_RE.findall(content):
                context = self._get_context(content, secret, 220)
                if self._is_valid_solana_secret_key(secret) and self._strong_secret_context(context):
                    vulns.append(Web3Vulnerability(
                        type="UPGRADE_AUTHORITY_EXPOSED",
                        severity="CRITICAL",
                        location=source,
                        description="Upgrade-authority-related secret key appears exposed",
                        evidence=f"Secret key candidate near upgrade authority context: {secret[:10]}...{secret[-8:]}",
                        remediation="Rotate authority, move to multisig/hardware custody, and remove frontend exposure",
                        exploitable=True,
                        potential_value="PROTOCOL TAKEOVER (10,000-1,000,000+ SOL)"
                    ))
                    return vulns

            # Address-only authority exposure is useful intel but not exploitable by itself.
            m = SOLANA_ADDRESS_RE.search(content)
            if m:
                vulns.append(Web3Vulnerability(
                    type="UPGRADE_AUTHORITY_REFERENCE",
                    severity="LOW",
                    location=source,
                    description="Upgrade authority reference found, but no private/secret key proof",
                    evidence=f"Authority-like address near upgrade authority text: {m.group(0)[:10]}...{m.group(0)[-8:]}",
                    remediation="Do not expose unnecessary authority metadata in frontend bundles",
                    exploitable=False,
                    potential_value="Requires leaked signing key"
                ))
                return vulns
        return vulns

    # Legacy compatibility checks kept for older pipeline callers.

    def check_rpc_url_exposure(self, target: str, rpc_urls: List[str]) -> List[Web3Vulnerability]:
        vulns: List[Web3Vulnerability] = []
        public_hosts = ["api.mainnet-beta.solana.com", "api.devnet.solana.com", "api.testnet.solana.com"]
        for rpc_url in rpc_urls:
            low = rpc_url.lower()
            if any(pub in low for pub in public_hosts):
                continue
            if any(x in low for x in ["private", "premium", "quicknode", "helius", "alchemy", "rpc.", "node."]):
                vulns.append(Web3Vulnerability(
                    type="PRIVATE_RPC_URL_EXPOSED",
                    severity="MEDIUM",
                    location="JavaScript Bundle",
                    description="Private/paid RPC URL exposed in frontend code",
                    evidence=f"RPC URL: {rpc_url[:70]}...",
                    remediation="Use server-side proxy or restrict RPC key/domain permissions",
                    exploitable=True,
                    potential_value="RPC quota/key abuse"
                ))
        return vulns

    def check_privy_auth_misconfig(self, target: str) -> List[Web3Vulnerability]:
        return self.check_privy_jwt_bypass(target)

    def check_socketio_timing_attack(self, target: str) -> List[Web3Vulnerability]:
        vulns: List[Web3Vulnerability] = []
        site_data = self.collect_site_data(target)
        combined = self._all_content(target, site_data).lower()
        if "socket.io" in combined:
            indicators = [i for i in ["serverseedhash", "clientseed", "multiplier", "crash"] if i in combined]
            if len(indicators) >= 2:
                vulns.append(Web3Vulnerability(
                    type="SOCKETIO_CRASH_GAME_DETECTED",
                    severity="HIGH",
                    location="Socket.IO Implementation",
                    description="Crash-game Socket.IO indicators found; timing attack surface exists",
                    evidence=f"Found indicators: {', '.join(indicators)}",
                    remediation="Use server-authoritative timing and commit-reveal randomness verification",
                    exploitable=False,
                    potential_value="Requires deeper timing proof"
                ))
        return vulns

    def check_wallet_drainer_vectors(self, target: str) -> List[Web3Vulnerability]:
        return self.check_wallet_drainer_xss(target)

    def check_token_approval_risks(self, target: str, program_ids: List[str]) -> List[Web3Vulnerability]:
        return self.check_unlimited_approvals(target)

    def run_all_web3_checks(self, target: str, site_data: Dict) -> List[Web3Vulnerability]:
        return self.run_real_exploit_scan(target, site_data)

    # ═══════════════════════════════════════════════════════════════════
    # 💰 EXPLOIT #6: PRIVY JWT BYPASS
    # ═══════════════════════════════════════════════════════════════════

    def check_privy_jwt_bypass(self, target: str, site_data: Optional[Dict] = None) -> List[Web3Vulnerability]:
        vulns: List[Web3Vulnerability] = []
        site_data = site_data or self.collect_site_data(target)
        combined = self._all_content(target, site_data)
        if "privy" not in combined.lower() and "jwt" not in combined.lower():
            return vulns

        secret_names = ["PRIVY_CLIENT_SECRET", "privyClientSecret", "PRIVY_APP_SECRET", "privy_secret"]
        for source, content in self._iter_content(target, site_data):
            for name in secret_names:
                pattern = re.compile(rf"{re.escape(name)}[\"']?\s*[:=]\s*[\"']([^\"'\s]{{12,}})[\"']", re.I)
                m = pattern.search(content)
                if m:
                    value = m.group(1)
                    if value.lower() not in ("undefined", "changeme", "example", "placeholder"):
                        vulns.append(Web3Vulnerability(
                            type="PRIVY_SECRET_EXPOSED",
                            severity="CRITICAL",
                            location=source,
                            description="Privy secret value exposed in frontend-accessible code",
                            evidence=f"{name} assigned a non-placeholder value: {value[:8]}... (redacted)",
                            remediation="Move Privy secret server-side and rotate it",
                            exploitable=True,
                            potential_value="ACCESS TO USER AUTH TOKENS (varies)"
                        ))
                        return vulns

            if re.search(r"\bjwt\.decode\s*\(", content, re.I) and not re.search(r"\b(jwt\.)?verify\s*\(", content, re.I):
                vulns.append(Web3Vulnerability(
                    type="JWT_NO_VERIFICATION",
                    severity="HIGH",
                    location=source,
                    description="JWT decode appears without nearby signature verification",
                    evidence="Found jwt.decode() but no verify() call in same source",
                    remediation="Always verify JWT signatures and reject alg=none",
                    exploitable=False,
                    potential_value="Requires endpoint-level auth bypass proof"
                ))
                return vulns
        return vulns

    # ═══════════════════════════════════════════════════════════════════
    # 💰 EXPLOIT #7: PHANTOM ORIGIN SPOOFING
    # ═══════════════════════════════════════════════════════════════════

    def check_phantom_origin_spoofing(self, target: str, site_data: Optional[Dict] = None) -> List[Web3Vulnerability]:
        vulns: List[Web3Vulnerability] = []
        site_data = site_data or self.collect_site_data(target)

        for source, content in self._iter_content(target, site_data):
            low = content.lower()
            if "window.open" not in content or not any(k in low for k in ("phantom", "wallet", "solana")):
                continue

            insecure = []
            if re.search(r"window\.open\([^)]*http://", content, re.I):
                insecure.append("wallet popup can use http://")
            if re.search(r"window\.open\([^)]*\+\s*\w+", content, re.I):
                insecure.append("wallet popup URL appears concatenated")
            if re.search(r"window\.open\([^)]*['_\"]_blank['_\"]", content, re.I) and "noopener" not in low:
                insecure.append("_blank popup without noopener evidence")

            if insecure:
                vulns.append(Web3Vulnerability(
                    type="PHANTOM_ORIGIN_SPOOFING",
                    severity="HIGH",
                    location=source,
                    description="Insecure wallet popup pattern found",
                    evidence="; ".join(insecure[:3]),
                    remediation="Use wallet-adapter standard methods, enforce HTTPS, and validate popup origin/opener behavior",
                    exploitable=True,
                    potential_value="100-1,000 SOL per victim (seed phrase theft)"
                ))
                return vulns
        return vulns

    # ═══════════════════════════════════════════════════════════════════
    # 💰 EXPLOIT #8: SIGNATURE REPLAY
    # ═══════════════════════════════════════════════════════════════════

    def check_signature_replay(self, target: str, site_data: Optional[Dict] = None) -> List[Web3Vulnerability]:
        vulns: List[Web3Vulnerability] = []
        site_data = site_data or self.collect_site_data(target)

        sign_terms = ["signTransaction", "signAllTransactions", "signAndSendTransaction"]
        protection_terms = ["recentBlockhash", "recent_blockhash", "lastValidBlockHeight", "nonce", "durableNonce"]

        for source, content in self._iter_content(target, site_data):
            if not any(term in content for term in sign_terms):
                continue
            # Look around signing calls. If protection appears anywhere in same bundle, do not flag.
            if any(term in content for term in protection_terms):
                continue

            vulns.append(Web3Vulnerability(
                type="SIGNATURE_REPLAY_VULNERABLE",
                severity="MEDIUM",
                location=source,
                description="Signing flow found without visible replay-protection keywords in the same source",
                evidence="signTransaction/signAllTransactions present; recentBlockhash/nonce terms absent in same source",
                remediation="Ensure every transaction includes a fresh recentBlockhash or durable nonce",
                exploitable=False,
                potential_value="1-50 SOL per transaction (requires transaction-level proof)"
            ))
            return vulns
        return vulns

    # ═══════════════════════════════════════════════════════════════════
    # 💰 EXPLOIT #9: UNENCRYPTED WEBSOCKET
    # ═══════════════════════════════════════════════════════════════════

    def check_unencrypted_websocket(self, target: str, site_data: Optional[Dict] = None) -> List[Web3Vulnerability]:
        vulns: List[Web3Vulnerability] = []
        site_data = site_data or self.collect_site_data(target)

        ws_pattern = re.compile(r"ws://[^\"'\s<>]+", re.I)
        for source, content in self._iter_content(target, site_data):
            for ws_url in ws_pattern.findall(content):
                if any(kw in ws_url.lower() for kw in ["solana", "rpc", "api", "node", "mainnet", "devnet"]):
                    vulns.append(Web3Vulnerability(
                        type="UNENCRYPTED_WEBSOCKET_RPC",
                        severity="MEDIUM",
                        location=source,
                        description="Unencrypted WebSocket RPC connection found",
                        evidence=f"Insecure URL: {ws_url[:80]}...",
                        remediation="Use wss:// for all RPC/WebSocket traffic",
                        exploitable=True,
                        potential_value="Varies (MITM transaction manipulation)"
                    ))
                    return vulns
        return vulns

    # ═══════════════════════════════════════════════════════════════════
    # 💰 EXPLOIT #10: HIGH SLIPPAGE
    # ═══════════════════════════════════════════════════════════════════

    def check_high_slippage(self, target: str, site_data: Optional[Dict] = None) -> List[Web3Vulnerability]:
        vulns: List[Web3Vulnerability] = []
        site_data = site_data or self.collect_site_data(target)

        slippage_patterns = [
            re.compile(r"(?:slippage|slippageTolerance|maxSlippage)[\"']?\s*[:=]\s*([0-9]+(?:\.[0-9]+)?)", re.I),
            re.compile(r"(?:slippageBps|slippage_bps)[\"']?\s*[:=]\s*([0-9]+)", re.I),
        ]

        for source, content in self._iter_content(target, site_data):
            low = content.lower()
            if not any(kw in low for kw in ["swap", "trade", "exchange", "dex", "jupiter", "raydium"]):
                continue

            for pattern in slippage_patterns:
                for m in pattern.finditer(content):
                    raw = float(m.group(1))
                    name = m.group(0).split(":")[0].split("=")[0]
                    # Handle basis points and percent without marking 50 bps as 50%.
                    if "bps" in name.lower():
                        percent = raw / 100.0
                    elif raw > 100:
                        percent = raw / 100.0
                    else:
                        percent = raw

                    if percent > 10:
                        vulns.append(Web3Vulnerability(
                            type="HIGH_SLIPPAGE_EXPLOIT",
                            severity="LOW",
                            location=source,
                            description=f"High slippage tolerance configured: {percent:g}%",
                            evidence=f"Raw slippage value {raw:g} resolved to {percent:g}%",
                            remediation="Use lower default slippage and require explicit user confirmation for high slippage",
                            exploitable=True,
                            potential_value="0.1-1 SOL per swap (slippage extraction)"
                        ))
                        return vulns
        return vulns

    # ═══════════════════════════════════════════════════════════════════
    # MASTER RUNNER - ALL 10 REAL EXPLOITS
    # ═══════════════════════════════════════════════════════════════════

    def run_real_exploit_scan(self, target: str, site_data: Optional[Dict] = None) -> List[Web3Vulnerability]:
        all_vulns: List[Web3Vulnerability] = []

        if site_data is None or not site_data.get("js_analysis"):
            site_data = self.collect_site_data(target)

        program_ids = site_data.get("js_analysis", {}).get("program_ids", [])
        js_bundles = site_data.get("js_analysis", {}).get("js_content", [])
        rpc_urls = site_data.get("js_analysis", {}).get("rpc_urls", [])

        print(f"\n  [💰] Running REAL exploit scan on {target}")
        print("  [→] Checking 10 high-value attack vectors...")
        print(f"  [→] Evidence collected: {len(js_bundles)} JS/source files, {len(program_ids)} program/address candidates, {len(rpc_urls)} RPC URLs")

        checks = [
            ("Wallet Drainer XSS", self.check_wallet_drainer_xss, (target, site_data)),
            ("Private Key Leaks", self.check_private_key_leaks, (target, js_bundles, site_data)),
            ("Unlimited Approvals", self.check_unlimited_approvals, (target, site_data)),
            ("Program ID Injection", self.check_program_id_injection, (target, program_ids, site_data)),
            ("Upgrade Authority Leaks", self.check_upgrade_authority_leaks, (target, program_ids, site_data)),
            ("Privy JWT Bypass", self.check_privy_jwt_bypass, (target, site_data)),
            ("Phantom Origin Spoofing", self.check_phantom_origin_spoofing, (target, site_data)),
            ("Signature Replay", self.check_signature_replay, (target, site_data)),
            ("Unencrypted WebSocket", self.check_unencrypted_websocket, (target, site_data)),
            ("High Slippage", self.check_high_slippage, (target, site_data)),
        ]

        for check_name, check_func, args in checks:
            try:
                print(f"    [→] {check_name}...", end=" ")
                vulns = check_func(*args)
                if vulns:
                    all_vulns.extend(vulns)
                    print(f"💀 FOUND {len(vulns)}")
                else:
                    print("✓")
            except Exception as e:
                print(f"✗ Error: {type(e).__name__}: {e}")

        if all_vulns:
            print(f"\n  [💀] TOTAL FINDINGS: {len(all_vulns)}")
            critical = sum(1 for v in all_vulns if v.severity == "CRITICAL")
            high = sum(1 for v in all_vulns if v.severity == "HIGH")
            medium = sum(1 for v in all_vulns if v.severity == "MEDIUM")
            low = sum(1 for v in all_vulns if v.severity == "LOW")
            confirmed = sum(1 for v in all_vulns if v.exploitable)
            print(f"  [💰] Critical: {critical} | High: {high} | Medium: {medium} | Low: {low} | Exploitable: {confirmed}")
        else:
            print("\n  [·] No exploitable vulnerabilities found")

        return all_vulns
