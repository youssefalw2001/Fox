#!/usr/bin/env python3
"""
FOX_PROOF_SCANNER.py

Proof-first scanner for authorized security testing of modern Web3 products.
Focus: Next.js/Vercel, Solana dApps, DeFi frontends, crash-game fairness signals,
gift-card abuse surfaces, and strict evidence reporting.

Design principles:
- Report confirmed evidence, not keyword guesses.
- Reject HTML fallback pages for file/secret findings.
- Keep passive/safe defaults. No destructive actions.
- Produce JSON and Markdown proof reports.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import re
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple
from urllib.parse import urljoin, urlparse

import requests


# -----------------------------
# Data model
# -----------------------------

@dataclass
class Finding:
    title: str
    severity: str
    confidence: int
    category: str
    location: str
    proof_type: str
    evidence: Dict[str, Any]
    impact: str
    remediation: str
    request: Optional[Dict[str, Any]] = None
    response_hash: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ScanOptions:
    target: str
    profile: str = "web3"
    timeout: int = 10
    delay: float = 0.15
    output_dir: str = "proof_output"
    min_confidence: int = 70
    user_agent: str = "FoxProofScanner/1.0 authorized-security-testing"


# -----------------------------
# Shared utilities
# -----------------------------

class HttpClient:
    def __init__(self, options: ScanOptions):
        self.options = options
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": options.user_agent})

    def get(self, url: str, **kwargs) -> Optional[requests.Response]:
        try:
            time.sleep(self.options.delay)
            return self.session.get(url, timeout=self.options.timeout, allow_redirects=True, **kwargs)
        except requests.RequestException:
            return None

    def head(self, url: str, **kwargs) -> Optional[requests.Response]:
        try:
            time.sleep(self.options.delay)
            return self.session.head(url, timeout=self.options.timeout, allow_redirects=False, **kwargs)
        except requests.RequestException:
            return None


def sha256_text(text: str) -> str:
    return hashlib.sha256((text or "").encode("utf-8", "replace")).hexdigest()


def is_html_response(text: str, headers: Optional[Dict[str, str]] = None) -> bool:
    body = text or ""
    prefix = body.lstrip()[:512].lower()
    if prefix.startswith("<!doctype") or prefix.startswith("<html"):
        return True
    if "<html" in prefix and ("<head" in prefix or "<body" in prefix or "</html>" in body.lower()[:4096]):
        return True
    ctype = ""
    if headers:
        ctype = (headers.get("content-type") or headers.get("Content-Type") or "").lower()
    return "text/html" in ctype and ("<html" in body.lower()[:4096] or "<!doctype" in body.lower()[:4096])


def extract_script_urls(base_url: str, html: str) -> List[str]:
    scripts = []
    for src in re.findall(r'<script[^>]+src=["\']([^"\']+)["\']', html or "", flags=re.I):
        scripts.append(urljoin(base_url, src))
    # Next.js build manifests often reference additional chunks.
    for src in re.findall(r'["\']([^"\']+\.js)["\']', html or "", flags=re.I):
        if src.startswith(("http://", "https://", "/", "./", "../")):
            scripts.append(urljoin(base_url, src))
    return sorted(set(scripts))


def redact(value: str, keep: int = 6) -> str:
    if not value:
        return ""
    if len(value) <= keep * 2:
        return value[:2] + "..."
    return value[:keep] + "..." + value[-keep:]


def b64url_json(part: str) -> Optional[dict]:
    try:
        padded = part + "=" * (-len(part) % 4)
        raw = base64.urlsafe_b64decode(padded.encode())
        parsed = json.loads(raw)
        return parsed if isinstance(parsed, dict) else None
    except Exception:
        return None


# -----------------------------
# Validators
# -----------------------------

PLACEHOLDER_RE = re.compile(r'^(your[_-]?|change[_-]?me|example|sample|null|undefined|none|todo|test|demo|x{4,}|\*{4,}|<.*?>|\${.*?})$', re.I)
SOLANA_ADDRESS_RE = re.compile(r'\b[1-9A-HJ-NP-Za-km-z]{32,44}\b')
SECRET_CONTEXT_RE = re.compile(r'(secret|private[_-]?key|keypair|seed|mnemonic|admin|treasury|authority|withdraw|signer|token|api[_-]?key|rpc)', re.I)


def find_valid_credentials(text: str) -> List[Tuple[str, str, str]]:
    """Return high-confidence credentials only: (kind, token, context)."""
    if not text or is_html_response(text):
        return []
    results: List[Tuple[str, str, str]] = []
    patterns = [
        ("STRIPE_LIVE_SECRET", r"\bsk_live_[A-Za-z0-9]{24}\b"),
        ("STRIPE_LIVE_PUBLIC", r"\bpk_live_[A-Za-z0-9]{24}\b"),
        ("AWS_ACCESS_KEY_ID", r"\bAKIA[0-9A-Z]{16}\b"),
        ("GOOGLE_API_KEY", r"\bAIza[0-9A-Za-z_\-]{35}\b"),
        ("JWT", r"\beyJ[A-Za-z0-9_\-]{8,}\.[A-Za-z0-9_\-]{8,}\.[A-Za-z0-9_\-]{8,}\b"),
        ("SOLANA_SECRET_KEY_ARRAY", r"(?:secretKey|privateKey|Keypair\.fromSecretKey|Uint8Array\.from)\s*\(?\s*\[\s*(?:\d{1,3}\s*,\s*){31,}\d{1,3}\s*\]"),
    ]
    seen: Set[str] = set()
    for kind, pattern in patterns:
        for m in re.finditer(pattern, text):
            token = m.group(0)
            if token in seen:
                continue
            if kind == "JWT":
                parts = token.split(".")
                header, payload = b64url_json(parts[0]), b64url_json(parts[1])
                if not header or not payload or "alg" not in header:
                    continue
            if kind == "AWS_ACCESS_KEY_ID" and not token[4:].isupper():
                continue
            ctx = text[max(0, m.start() - 80): min(len(text), m.end() + 80)]
            seen.add(token)
            results.append((kind, token, ctx))
    return results


def classify_solana_addresses(text: str) -> List[Dict[str, Any]]:
    """Extract Solana-like addresses and classify by surrounding context."""
    items = []
    if not text or is_html_response(text):
        return items
    for m in SOLANA_ADDRESS_RE.finditer(text):
        addr = m.group(0)
        # Reject obvious all-ones program/system placeholders unless context matters.
        ctx = text[max(0, m.start() - 90): min(len(text), m.end() + 90)]
        ctx_low = ctx.lower()
        role = "public_address"
        severity_hint = "INFO"
        if re.search(r'upgrade[_-]?authority|program[_-]?authority', ctx_low):
            role, severity_hint = "upgrade_or_program_authority", "HIGH"
        elif re.search(r'treasury|vault|fee[_-]?wallet|withdraw', ctx_low):
            role, severity_hint = "treasury_or_vault_wallet", "MEDIUM"
        elif re.search(r'admin|owner|operator|authority|signer', ctx_low):
            role, severity_hint = "admin_or_authority_wallet", "MEDIUM"
        items.append({"address": addr, "role": role, "severity_hint": severity_hint, "context": ctx.strip()[:220]})
    # Deduplicate by address+role.
    dedup = {}
    for item in items:
        dedup[(item["address"], item["role"])] = item
    return list(dedup.values())


def validate_source_map(text: str, headers: Dict[str, str]) -> Optional[Dict[str, Any]]:
    if not text or is_html_response(text, headers):
        return None
    try:
        data = json.loads(text)
    except Exception:
        return None
    if not isinstance(data, dict):
        return None
    sources = data.get("sources")
    mappings = data.get("mappings")
    if isinstance(sources, list) and len(sources) > 0 and isinstance(mappings, str) and len(mappings) > 20:
        sensitive_sources = [s for s in sources if any(x in str(s).lower() for x in ["api", "auth", "admin", "wallet", "seed", "server", "privy", "config"])]
        return {
            "source_count": len(sources),
            "sensitive_source_examples": sensitive_sources[:8],
            "first_sources": sources[:8],
        }
    return None


def validate_next_manifest(text: str, headers: Dict[str, str]) -> Optional[Dict[str, Any]]:
    if not text or is_html_response(text, headers):
        return None
    try:
        data = json.loads(text)
    except Exception:
        return None
    if isinstance(data, dict) and ("pages" in data or "sortedPages" in data or "__rewrites" in data):
        routes = []
        for key in ("sortedPages", "pages"):
            val = data.get(key)
            if isinstance(val, list):
                routes.extend([str(x) for x in val])
            elif isinstance(val, dict):
                routes.extend([str(x) for x in val.keys()])
        interesting = [r for r in routes if re.search(r'(admin|api|auth|wallet|debug|test|internal)', r, re.I)]
        return {"route_count": len(routes), "interesting_routes": interesting[:20]}
    return None


def validate_socketio_handshake(text: str, headers: Dict[str, str]) -> Optional[Dict[str, Any]]:
    if not text or is_html_response(text, headers):
        return None
    # Engine.IO polling open packet often begins with 0{"sid":"...","upgrades":...
    cleaned = text.strip()
    if cleaned.startswith("0{") and '"sid"' in cleaned and '"upgrades"' in cleaned:
        return {"handshake": cleaned[:220]}
    if "Session ID unknown" in cleaned or "Transport unknown" in cleaned:
        return {"handshake_error": cleaned[:160], "note": "Socket.IO endpoint exists but did not open unauthenticated polling session"}
    return None


def validate_seed_timing_blob(text: str) -> List[Dict[str, Any]]:
    """Inspect already fetched public text for dangerous pre-round/fairness terms.
    This is a static/passive signal, not a live game interaction.
    """
    if not text or is_html_response(text):
        return []
    findings = []
    patterns = [
        ("serverSeed_static_reference", r"serverSeed"),
        ("nextSeed_static_reference", r"nextSeed"),
        ("test_get_state_reference", r"test:getState|game:standard:test:getState"),
        ("provably_fair_reference", r"provablyFair|serverSeedHash|externalHash"),
    ]
    for name, pattern in patterns:
        for m in re.finditer(pattern, text, re.I):
            ctx = text[max(0, m.start() - 120): min(len(text), m.end() + 120)]
            findings.append({"signal": name, "context": ctx[:260]})
            break
    return findings


def validate_env_lines(text: str) -> List[Dict[str, str]]:
    if not text or is_html_response(text):
        return []
    out = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key, value = key.strip(), value.strip().strip('"\'')
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{1,80}", key):
            continue
        if PLACEHOLDER_RE.fullmatch(value) or len(value) < 11:
            continue
        if SECRET_CONTEXT_RE.search(key):
            out.append({"key": key, "value_redacted": redact(value)})
    return out


# -----------------------------
# Scanner implementation
# -----------------------------

class FoxProofScanner:
    def __init__(self, options: ScanOptions):
        self.options = options
        self.client = HttpClient(options)
        self.findings: List[Finding] = []
        self.visited_js: Set[str] = set()

    def add(self, finding: Finding):
        if finding.confidence >= self.options.min_confidence:
            self.findings.append(finding)

    def scan(self) -> List[Finding]:
        target = self.options.target.rstrip("/") + "/"
        profile = self.options.profile.lower()

        if profile in ("web", "web3", "vercel-next", "solana-dapp", "defi", "crash-game", "giftcard", "all"):
            self.scan_base_page(target)
            self.scan_next_vercel(target)
            self.scan_sensitive_static_files(target)

        if profile in ("web3", "solana-dapp", "defi", "crash-game", "all"):
            self.scan_web3_static_surface(target)
            self.scan_socketio_surface(target)

        if profile in ("crash-game", "all"):
            self.scan_crash_game_static_signals(target)

        if profile in ("giftcard", "all"):
            self.scan_giftcard_surface(target)

        self.dedupe()
        return self.findings

    def scan_base_page(self, target: str):
        r = self.client.get(target)
        if not r:
            return
        body = r.text or ""
        scripts = extract_script_urls(target, body)
        headers = dict(r.headers)

        missing = []
        for h in ["Content-Security-Policy", "Strict-Transport-Security", "X-Content-Type-Options", "X-Frame-Options", "Referrer-Policy"]:
            if h not in headers:
                missing.append(h)
        if missing:
            self.add(Finding(
                title="Missing browser security headers",
                severity="LOW",
                confidence=80,
                category="web_hardening",
                location=target,
                proof_type="header_absence",
                evidence={"missing_headers": missing},
                impact="Missing headers can weaken browser-side protections and increase impact of other bugs.",
                remediation="Add a strict CSP, HSTS, X-Content-Type-Options, X-Frame-Options or frame-ancestors, and Referrer-Policy.",
                request={"method": "GET", "url": target},
                response_hash=sha256_text(body),
            ))

        for js in scripts[:40]:
            self.scan_js_file(js)

    def scan_js_file(self, js_url: str):
        if js_url in self.visited_js:
            return
        self.visited_js.add(js_url)
        r = self.client.get(js_url)
        if not r or r.status_code != 200 or is_html_response(r.text, r.headers):
            return
        text = r.text or ""

        creds = find_valid_credentials(text)
        for kind, token, ctx in creds[:5]:
            severity = "CRITICAL" if kind in {"STRIPE_LIVE_SECRET", "AWS_ACCESS_KEY_ID", "SOLANA_SECRET_KEY_ARRAY"} else "HIGH"
            self.add(Finding(
                title=f"High-confidence credential pattern in JavaScript: {kind}",
                severity=severity,
                confidence=95,
                category="frontend_secret_exposure",
                location=js_url,
                proof_type="specific_credential_format",
                evidence={"kind": kind, "token_redacted": redact(token), "context": ctx[:220]},
                impact="A real credential-like value is present in client-accessible JavaScript and may need rotation or restriction.",
                remediation="Remove secrets from client bundles, rotate exposed credentials, and use server-side proxying for private keys.",
                request={"method": "GET", "url": js_url},
                response_hash=sha256_text(text),
            ))

        addresses = classify_solana_addresses(text)
        important = [a for a in addresses if a["severity_hint"] in ("HIGH", "MEDIUM")]
        if important:
            top = important[:10]
            self.add(Finding(
                title="Solana authority/treasury-like addresses exposed in frontend context",
                severity="MEDIUM" if all(x["severity_hint"] == "MEDIUM" for x in top) else "HIGH",
                confidence=82,
                category="solana_static_mapping",
                location=js_url,
                proof_type="address_context_classification",
                evidence={"addresses": top},
                impact="Authority, treasury, or admin wallet references in frontend code help map high-value control points and may reveal centralization risk.",
                remediation="Keep public addresses documented intentionally; remove misleading admin labels and ensure authority wallets are multisig/timelocked where possible.",
                request={"method": "GET", "url": js_url},
                response_hash=sha256_text(text),
            ))

        rpc_urls = sorted(set(re.findall(r"https://[A-Za-z0-9_.\-/]*?(?:helius|quicknode|alchemy|ankr|rpcpool|triton|mainnet-beta\.solana)[A-Za-z0-9_.\-/?=&%]*", text, re.I)))
        if rpc_urls:
            self.add(Finding(
                title="Solana RPC endpoints disclosed in frontend",
                severity="INFO",
                confidence=90,
                category="solana_rpc_surface",
                location=js_url,
                proof_type="rpc_url_extraction",
                evidence={"rpc_urls": [u[:140] for u in rpc_urls[:10]]},
                impact="Public RPC URLs are often expected, but provider keys should be restricted by domain and quota.",
                remediation="Apply provider-side domain allowlists, method restrictions, rate limits, and monitor usage.",
                request={"method": "GET", "url": js_url},
                response_hash=sha256_text(text),
            ))

        for map_url in [js_url + ".map"]:
            self.scan_source_map(map_url)

    def scan_next_vercel(self, target: str):
        paths = [
            "/_next/static/development/_buildManifest.js",
            "/_next/static/development/_ssgManifest.js",
            "/_next/routes-manifest.json",
            "/_next/build-manifest.json",
            "/_next/prerender-manifest.json",
        ]
        for path in paths:
            url = urljoin(target, path)
            r = self.client.get(url)
            if not r or r.status_code != 200:
                continue
            manifest = validate_next_manifest(r.text, r.headers)
            if manifest:
                interesting = manifest.get("interesting_routes", [])
                self.add(Finding(
                    title="Next.js manifest exposed",
                    severity="LOW" if not interesting else "MEDIUM",
                    confidence=86,
                    category="nextjs_vercel",
                    location=url,
                    proof_type="valid_next_manifest",
                    evidence=manifest,
                    impact="Build manifests can reveal routes and client chunks; sensitive route names may help targeted testing.",
                    remediation="Avoid shipping sensitive route names and ensure server/API routes enforce authorization regardless of obscurity.",
                    request={"method": "GET", "url": url},
                    response_hash=sha256_text(r.text),
                ))

    def scan_source_map(self, map_url: str):
        r = self.client.get(map_url)
        if not r or r.status_code != 200:
            return
        proof = validate_source_map(r.text, r.headers)
        if proof:
            severity = "HIGH" if proof.get("sensitive_source_examples") else "MEDIUM"
            self.add(Finding(
                title="JavaScript source map exposed",
                severity=severity,
                confidence=92,
                category="source_map_exposure",
                location=map_url,
                proof_type="valid_source_map_json",
                evidence=proof,
                impact="Source maps can expose original source paths and implementation details, making business logic and hidden routes easier to audit or attack.",
                remediation="Disable production source maps or restrict access to them.",
                request={"method": "GET", "url": map_url},
                response_hash=sha256_text(r.text),
            ))

    def scan_sensitive_static_files(self, target: str):
        for path in ["/.env", "/.env.local", "/.env.production", "/.git/HEAD", "/.git/config"]:
            url = urljoin(target, path)
            r = self.client.get(url)
            if not r or r.status_code in (403, 404) or r.status_code != 200 or is_html_response(r.text, r.headers):
                continue
            if path.startswith("/.env"):
                envs = validate_env_lines(r.text)
                if envs:
                    self.add(Finding(
                        title="Environment file with real-looking secret values exposed",
                        severity="CRITICAL",
                        confidence=98,
                        category="sensitive_file_exposure",
                        location=url,
                        proof_type="env_key_value_secret_validation",
                        evidence={"secrets": envs[:10]},
                        impact="Public environment files can expose credentials, tokens, and internal service URLs.",
                        remediation="Block dotfiles at the CDN/web server layer and rotate every exposed value.",
                        request={"method": "GET", "url": url},
                        response_hash=sha256_text(r.text),
                    ))
            elif path.endswith("HEAD"):
                first = (r.text or "").strip().splitlines()[0] if r.text.strip() else ""
                if first.startswith("ref:") and "refs/" in first:
                    self.add(Finding(
                        title="Git repository HEAD exposed",
                        severity="CRITICAL",
                        confidence=99,
                        category="sensitive_file_exposure",
                        location=url,
                        proof_type="git_head_format",
                        evidence={"head": first},
                        impact="Exposed Git metadata may allow source reconstruction if object files are accessible.",
                        remediation="Block .git paths and remove repository metadata from web roots.",
                        request={"method": "GET", "url": url},
                        response_hash=sha256_text(r.text),
                    ))
            elif path.endswith("config"):
                low = r.text.lower()
                if "[core]" in low and "repositoryformatversion" in low:
                    self.add(Finding(
                        title="Git config exposed",
                        severity="CRITICAL",
                        confidence=99,
                        category="sensitive_file_exposure",
                        location=url,
                        proof_type="git_config_format",
                        evidence={"snippet": r.text[:300]},
                        impact="Exposed Git config confirms repository metadata is accessible from the web root.",
                        remediation="Block .git paths and remove repository metadata from web roots.",
                        request={"method": "GET", "url": url},
                        response_hash=sha256_text(r.text),
                    ))

    def scan_web3_static_surface(self, target: str):
        r = self.client.get(target)
        if not r:
            return
        text = r.text or ""
        signals = []
        for term in ["privy", "phantom", "solana", "wallet-adapter", "anchor", "programId", "treasury", "vault"]:
            if re.search(term, text, re.I):
                signals.append(term)
        if signals:
            self.add(Finding(
                title="Web3/Solana frontend fingerprint",
                severity="INFO",
                confidence=85,
                category="web3_fingerprint",
                location=target,
                proof_type="static_keyword_fingerprint",
                evidence={"signals": signals},
                impact="Confirms the relevant Web3 scan profile and helps select Solana/Privy/Wallet checks.",
                remediation="Informational only. Ensure all wallet and program interactions are server-validated where required.",
                request={"method": "GET", "url": target},
                response_hash=sha256_text(text),
            ))

    def scan_socketio_surface(self, target: str):
        base = target.rstrip("/")
        for path in ["/socket.io/?EIO=4&transport=polling", "/socket.io/?EIO=3&transport=polling"]:
            url = base + path
            r = self.client.get(url)
            if not r or r.status_code not in (200, 400):
                continue
            proof = validate_socketio_handshake(r.text, r.headers)
            if proof:
                severity = "MEDIUM" if "handshake" in proof else "INFO"
                confidence = 88 if "handshake" in proof else 75
                self.add(Finding(
                    title="Socket.IO endpoint detected",
                    severity=severity,
                    confidence=confidence,
                    category="websocket_surface",
                    location=url,
                    proof_type="engineio_handshake_or_error",
                    evidence=proof,
                    impact="A live Socket.IO endpoint exists. For game/financial apps, event authorization and payload filtering should be reviewed.",
                    remediation="Require authentication/authorization per event and never emit private state to public subscribers.",
                    request={"method": "GET", "url": url},
                    response_hash=sha256_text(r.text),
                ))

    def scan_crash_game_static_signals(self, target: str):
        r = self.client.get(target)
        if not r:
            return
        blobs = [(target, r.text or "")]
        for js in extract_script_urls(target, r.text or "")[:30]:
            jr = self.client.get(js)
            if jr and jr.status_code == 200 and not is_html_response(jr.text, jr.headers):
                blobs.append((js, jr.text or ""))
        for location, text in blobs:
            signals = validate_seed_timing_blob(text)
            dangerous = [s for s in signals if s["signal"] in {"serverSeed_static_reference", "nextSeed_static_reference", "test_get_state_reference"}]
            if dangerous:
                self.add(Finding(
                    title="Crash-game seed/state terms present in client-accessible code",
                    severity="HIGH",
                    confidence=82,
                    category="crash_game_fairness_review",
                    location=location,
                    proof_type="static_seed_state_signal",
                    evidence={"signals": dangerous[:8]},
                    impact="Client-accessible references to seed/state fields require manual timing verification to ensure seeds are never visible before round settlement.",
                    remediation="Verify serverSeed/nextSeed are never emitted before settlement; expose only commitments pre-round and reveal seeds post-round.",
                    request={"method": "GET", "url": location},
                    response_hash=sha256_text(text),
                ))

    def scan_giftcard_surface(self, target: str):
        r = self.client.get(target)
        if not r:
            return
        text = r.text or ""
        scripts = extract_script_urls(target, text)
        combined = text
        for js in scripts[:25]:
            jr = self.client.get(js)
            if jr and jr.status_code == 200 and not is_html_response(jr.text, jr.headers):
                combined += "\n" + jr.text[:200000]
        gift_terms = re.findall(r"\b(?:gift\s*card|giftcard|redeem|redemption|promo|coupon|voucher|balance\s*check|cardNumber|pin)\b", combined, re.I)
        endpoint_like = sorted(set(re.findall(r"[\"'](/[^\"']*(?:gift|redeem|promo|coupon|voucher|balance)[^\"']*)[\"']", combined, re.I)))
        if gift_terms or endpoint_like:
            self.add(Finding(
                title="Gift-card / promo abuse surface detected",
                severity="INFO",
                confidence=84,
                category="giftcard_surface",
                location=target,
                proof_type="static_business_logic_surface",
                evidence={"terms_found": sorted(set([t.lower() for t in gift_terms]))[:20], "candidate_endpoints": endpoint_like[:20]},
                impact="Gift-card and promo flows need rate limits, anti-enumeration responses, signed webhooks, and abuse monitoring.",
                remediation="Apply per-account/IP/device limits, generic error messages, webhook signatures, and velocity monitoring.",
                request={"method": "GET", "url": target},
                response_hash=sha256_text(combined[:200000]),
            ))

    def dedupe(self):
        seen = set()
        unique = []
        for f in self.findings:
            key = (f.title, f.location, f.proof_type, json.dumps(f.evidence, sort_keys=True)[:300])
            if key in seen:
                continue
            seen.add(key)
            unique.append(f)
        sev_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "INFO": 4}
        self.findings = sorted(unique, key=lambda x: (sev_order.get(x.severity, 9), -x.confidence, x.title))

    def write_reports(self) -> Tuple[str, str]:
        os.makedirs(self.options.output_dir, exist_ok=True)
        stamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        base = urlparse(self.options.target).netloc.replace(":", "_") or "target"
        json_path = os.path.join(self.options.output_dir, f"{base}_{stamp}_findings.json")
        md_path = os.path.join(self.options.output_dir, f"{base}_{stamp}_report.md")

        data = {
            "target": self.options.target,
            "profile": self.options.profile,
            "min_confidence": self.options.min_confidence,
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "finding_count": len(self.findings),
            "findings": [f.to_dict() for f in self.findings],
        }
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        with open(md_path, "w", encoding="utf-8") as f:
            f.write(f"# Fox Proof Scanner Report\n\n")
            f.write(f"- Target: `{self.options.target}`\n")
            f.write(f"- Profile: `{self.options.profile}`\n")
            f.write(f"- Findings: `{len(self.findings)}`\n")
            f.write(f"- Generated: `{data['generated_at']}`\n\n")
            for i, finding in enumerate(self.findings, 1):
                f.write(f"## {i}. {finding.title}\n\n")
                f.write(f"- Severity: **{finding.severity}**\n")
                f.write(f"- Confidence: **{finding.confidence}%**\n")
                f.write(f"- Category: `{finding.category}`\n")
                f.write(f"- Location: `{finding.location}`\n")
                f.write(f"- Proof type: `{finding.proof_type}`\n")
                f.write(f"- Impact: {finding.impact}\n")
                f.write(f"- Remediation: {finding.remediation}\n\n")
                f.write("```json\n")
                f.write(json.dumps(finding.evidence, indent=2)[:3000])
                f.write("\n```\n\n")
        return json_path, md_path


def parse_args() -> ScanOptions:
    parser = argparse.ArgumentParser(description="Fox Proof Scanner - strict Web3/Solana evidence scanner")
    parser.add_argument("--target", "-t", required=True, help="Target base URL, e.g. https://example.com")
    parser.add_argument("--profile", default="web3", choices=["web", "web3", "vercel-next", "solana-dapp", "defi", "crash-game", "giftcard", "all"])
    parser.add_argument("--timeout", type=int, default=10)
    parser.add_argument("--delay", type=float, default=0.15)
    parser.add_argument("--output", default="proof_output")
    parser.add_argument("--min-confidence", type=int, default=70)
    args = parser.parse_args()
    return ScanOptions(
        target=args.target,
        profile=args.profile,
        timeout=args.timeout,
        delay=args.delay,
        output_dir=args.output,
        min_confidence=args.min_confidence,
    )


def main():
    options = parse_args()
    scanner = FoxProofScanner(options)
    findings = scanner.scan()
    json_path, md_path = scanner.write_reports()
    print(f"\nFox Proof Scanner complete")
    print(f"Target: {options.target}")
    print(f"Profile: {options.profile}")
    print(f"Findings: {len(findings)}")
    for f in findings:
        print(f"[{f.severity}] {f.confidence}% {f.title} -> {f.location}")
    print(f"\nJSON: {json_path}")
    print(f"Markdown: {md_path}")


if __name__ == "__main__":
    main()
