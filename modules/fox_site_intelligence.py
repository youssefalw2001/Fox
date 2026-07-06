#!/usr/bin/env python3
from __future__ import annotations

import base64
import hashlib
import json
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple
from urllib.parse import urljoin, urlparse

import requests

URL_RE = re.compile(r"https?://[^\s\"'<>]+", re.I)
HREF_RE = re.compile(r"(?:href|src|action)=[\"']([^\"']+)[\"']", re.I)
SCRIPT_RE = re.compile(r"<script[^>]+src=[\"']([^\"']+\.js[^\"']*)[\"']", re.I)
ROUTE_RE = re.compile(r"[\"']((?:/|https?://)[A-Za-z0-9_./?=&:%+\-#]{3,220})[\"']")
GRAPHQL_RE = re.compile(r"\b(query|mutation|subscription)\s+[A-Za-z0-9_]+", re.I)
KEY_VALUE_RE = re.compile(r"(?m)^\s*([A-Z0-9_]{3,60})\s*=\s*([^\n\r]{4,200})\s*$")
JWT_RE = re.compile(r"eyJ[A-Za-z0-9_\-]{8,}\.[A-Za-z0-9_\-]{8,}\.[A-Za-z0-9_\-]{8,}")

STATIC_EXTENSIONS = (
    ".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".ico", ".css",
    ".woff", ".woff2", ".ttf", ".pdf", ".zip", ".gz", ".tar", ".mp4",
)

INTERESTING_PATHS = [
    "/robots.txt", "/sitemap.xml", "/.env", "/.env.local", "/.env.production",
    "/config.json", "/settings.json", "/manifest.json", "/swagger.json", "/openapi.json",
    "/api/docs", "/docs", "/graphql", "/api/graphql", "/admin", "/dashboard",
    "/api/admin", "/api/internal", "/api/debug", "/debug", "/health", "/status",
]

ADMIN_WORDS = ["admin", "internal", "staff", "moderator", "superuser", "root", "manage", "dashboard"]
AUTH_WORDS = ["token", "authorization", "bearer", "cookie", "session", "jwt", "apikey", "api_key"]
WEB3_MARKERS = [
    "window.solana", "isPhantom", "PhantomProvider", "@solana/wallet-adapter",
    "wallet-adapter-react", "solanaWeb3", "mainnet-beta", "signMessage",
    "signTransaction", "sendTransaction", "programId", "slippage", "rpc",
]
SECRET_NAMES = ["SECRET", "TOKEN", "PRIVATE", "PASSWORD", "API_KEY", "ACCESS_KEY", "DATABASE_URL", "STRIPE", "AWS", "SUPABASE"]


@dataclass
class HTTPObservation:
    url: str
    status: int
    content_type: str
    length: int
    title: str = ""
    body_hash: str = ""


@dataclass
class Finding:
    type: str
    severity: str
    title: str
    location: str
    evidence: str
    confidence: int
    impact: str
    remediation: str
    source: str = "fox_site_intelligence"
    false_positive_risk: str = "LOW"
    attacker_value: str = ""
    proof: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SiteMap:
    target: str
    pages: List[HTTPObservation] = field(default_factory=list)
    scripts: List[str] = field(default_factory=list)
    endpoints: List[str] = field(default_factory=list)
    admin_candidates: List[str] = field(default_factory=list)
    graphql_candidates: List[str] = field(default_factory=list)
    swagger_candidates: List[str] = field(default_factory=list)
    web3_markers: List[str] = field(default_factory=list)
    js_blobs: Dict[str, str] = field(default_factory=dict)


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def normalize_url(value: str, base: Optional[str] = None) -> Optional[str]:
    value = (value or "").strip().strip("'\"")
    if not value:
        return None
    if base:
        value = urljoin(base, value)
    if value.startswith("//"):
        value = "https:" + value
    if not value.startswith(("http://", "https://")):
        return None
    parsed = urlparse(value)
    if not parsed.netloc:
        return None
    if parsed.path.lower().endswith(STATIC_EXTENSIONS):
        return None
    return f"{parsed.scheme}://{parsed.netloc}{parsed.path or ''}".rstrip("/")


def same_origin(a: str, b: str) -> bool:
    return urlparse(a).netloc.lower() == urlparse(b).netloc.lower()


def body_hash(text: str) -> str:
    return hashlib.sha1((text or "").encode("utf-8", errors="ignore")).hexdigest()[:16]


def redacted(value: Any) -> str:
    text = str(value or "")
    text = JWT_RE.sub(lambda m: m.group(0)[:8] + "...<redacted-jwt>", text)
    text = re.sub(r"(?i)(password|secret|token|api[_-]?key)([\"']?\s*[:=]\s*[\"']?)([^\s\"']{8,})", r"\1\2<redacted>", text)
    return text[:500]


class AuthContext:
    def __init__(self, headers: Optional[Dict[str, str]] = None, cookies: Optional[Dict[str, str]] = None, name: str = "public"):
        self.headers = headers or {}
        self.cookies = cookies or {}
        self.name = name

    @classmethod
    def from_files(cls, headers_path: Optional[str] = None, cookies_path: Optional[str] = None, name: str = "user") -> "AuthContext":
        headers: Dict[str, str] = {}
        cookies: Dict[str, str] = {}
        if headers_path:
            headers = json.loads(Path(headers_path).read_text(encoding="utf-8"))
        if cookies_path:
            cookies = json.loads(Path(cookies_path).read_text(encoding="utf-8"))
        return cls(headers=headers, cookies=cookies, name=name)


class FoxSiteIntelligence:
    def __init__(self, target: str, timeout: int = 8, max_pages: int = 60, deep: bool = False):
        self.target = normalize_url(target) or target.rstrip("/")
        self.timeout = timeout
        self.max_pages = max_pages
        self.deep = deep
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "FoxSiteIntelligence/1.0 (+authorized-assessment)"})
        self.sitemap = SiteMap(target=self.target)
        self.findings: List[Finding] = []

    def fetch(self, url: str, ctx: Optional[AuthContext] = None, method: str = "GET") -> Tuple[HTTPObservation, str]:
        ctx = ctx or AuthContext()
        try:
            response = self.session.request(method, url, timeout=self.timeout, headers=ctx.headers, cookies=ctx.cookies, allow_redirects=True)
            text = response.text[:1_000_000]
            title_match = re.search(r"<title[^>]*>(.*?)</title>", text, re.I | re.S)
            title = re.sub(r"\s+", " ", title_match.group(1)).strip() if title_match else ""
            obs = HTTPObservation(
                url=response.url,
                status=response.status_code,
                content_type=response.headers.get("content-type", ""),
                length=len(response.content),
                title=title[:120],
                body_hash=body_hash(text),
            )
            return obs, text
        except Exception as exc:
            return HTTPObservation(url=url, status=0, content_type="", length=0, title=str(exc)[:120], body_hash=""), ""

    def crawl(self) -> SiteMap:
        queue: List[str] = [self.target]
        for path in INTERESTING_PATHS:
            queue.append(urljoin(self.target + "/", path.lstrip("/")))
        seen: Set[str] = set()

        while queue and len(seen) < self.max_pages:
            url = normalize_url(queue.pop(0))
            if not url or url in seen or not same_origin(url, self.target):
                continue
            seen.add(url)
            obs, text = self.fetch(url)
            self.sitemap.pages.append(obs)
            if obs.status and obs.status < 500:
                self.extract_from_text(url, text)
                if self.deep:
                    for link in HREF_RE.findall(text)[:80]:
                        u = normalize_url(link, base=url)
                        if u and same_origin(u, self.target) and u not in seen:
                            queue.append(u)
        self.sitemap.endpoints = sorted(set(self.sitemap.endpoints))
        self.sitemap.admin_candidates = sorted(set(self.sitemap.admin_candidates))
        self.sitemap.graphql_candidates = sorted(set(self.sitemap.graphql_candidates))
        self.sitemap.swagger_candidates = sorted(set(self.sitemap.swagger_candidates))
        self.sitemap.web3_markers = sorted(set(self.sitemap.web3_markers))
        return self.sitemap

    def extract_from_text(self, base_url: str, text: str) -> None:
        low = text.lower()
        for script in SCRIPT_RE.findall(text):
            js_url = normalize_url(script, base=base_url)
            if js_url and same_origin(js_url, self.target):
                self.sitemap.scripts.append(js_url)
                _, js_text = self.fetch(js_url)
                self.sitemap.js_blobs[js_url] = js_text[:1_000_000]
                self.extract_routes_from_blob(js_url, js_text)
        self.extract_routes_from_blob(base_url, text)
        for marker in WEB3_MARKERS:
            if marker.lower() in low:
                self.sitemap.web3_markers.append(marker)

    def extract_routes_from_blob(self, base_url: str, text: str) -> None:
        for raw in ROUTE_RE.findall(text or "")[:800]:
            u = normalize_url(raw, base=base_url)
            if not u or not same_origin(u, self.target):
                continue
            self.sitemap.endpoints.append(u)
            path = urlparse(u).path.lower()
            if any(word in path for word in ADMIN_WORDS):
                self.sitemap.admin_candidates.append(u)
            if "graphql" in path or GRAPHQL_RE.search(text or ""):
                self.sitemap.graphql_candidates.append(u)
            if "swagger" in path or "openapi" in path:
                self.sitemap.swagger_candidates.append(u)
        for raw in URL_RE.findall(text or "")[:500]:
            u = normalize_url(raw)
            if u and same_origin(u, self.target):
                self.sitemap.endpoints.append(u)

    def run_exposure_checks(self) -> None:
        for obs in self.sitemap.pages:
            path = urlparse(obs.url).path.lower()
            if obs.status == 200 and any(x in path for x in [".env", "config", "settings"]):
                _, text = self.fetch(obs.url)
                kv = KEY_VALUE_RE.findall(text)
                sensitive = [k for k, _ in kv if any(name in k.upper() for name in SECRET_NAMES)]
                if len(kv) >= 3 and sensitive and "text/html" not in obs.content_type.lower():
                    self.add_finding("EXPOSED_CONFIG", "CRITICAL", "Exposed environment/config file", obs.url,
                                     f"{len(kv)} key=value lines, sensitive keys: {', '.join(sensitive[:5])}", 94,
                                     "Secrets may allow API abuse, cloud abuse, data access, or payment abuse.",
                                     "Remove public access, rotate exposed secrets, and serve config only server-side.")
            if obs.status == 200 and ("swagger" in path or "openapi" in path or "api/docs" in path):
                self.add_finding("API_DOCUMENTATION_EXPOSED", "MEDIUM", "Public API documentation", obs.url,
                                 f"Public docs endpoint returned HTTP 200 ({obs.content_type})", 72,
                                 "Attackers can map endpoints and parameters faster.",
                                 "Restrict sensitive docs or remove internal operations from public schemas.")
            if obs.status == 200 and "graphql" in path:
                self.add_finding("GRAPHQL_ENDPOINT_DISCOVERED", "MEDIUM", "GraphQL endpoint discovered", obs.url,
                                 "GraphQL endpoint responded publicly; test auth boundaries and introspection.", 68,
                                 "Attackers may enumerate schema or abuse weak resolver authorization.",
                                 "Disable introspection in production if not needed and enforce resolver-level authorization.")

    def run_js_intelligence(self) -> None:
        combined = "\n".join(self.sitemap.js_blobs.values())
        if not combined:
            return
        for marker in WEB3_MARKERS:
            if marker.lower() in combined.lower():
                self.add_finding("WEB3_FRONTEND_LOGIC", "MEDIUM", "Web3 wallet logic detected", "frontend JavaScript",
                                 f"Detected marker: {marker}", 70,
                                 "Wallet/signature logic in frontend needs review for signing, slippage, and transaction safety.",
                                 "Review transaction construction, nonce/domain binding, slippage controls, and wallet prompts.")
        for match in KEY_VALUE_RE.findall(combined):
            key, val = match
            if any(name in key.upper() for name in SECRET_NAMES):
                self.add_finding("FRONTEND_SECRET_LIKE_VALUE", "HIGH", "Secret-like frontend variable", "frontend JavaScript",
                                 redacted(f"{key}={val}"), 76,
                                 "Frontend-exposed keys may allow API abuse if they are privileged.",
                                 "Move privileged secrets server-side; verify exposed keys are public/restricted.", false_positive_risk="MEDIUM")
                break
        admin_hits = [u for u in self.sitemap.admin_candidates][:10]
        if admin_hits:
            self.add_finding("ADMIN_SURFACE_DISCOVERED", "LOW", "Admin/internal routes referenced by site", "frontend/routes",
                             "\n".join(admin_hits), 62,
                             "Admin route names help attackers map protected attack surface.",
                             "Ensure server-side authorization on every admin/internal endpoint.", false_positive_risk="MEDIUM")

    def run_header_and_cors_checks(self) -> None:
        root = self.sitemap.pages[0] if self.sitemap.pages else None
        if not root:
            return
        try:
            r = self.session.get(self.target, timeout=self.timeout, headers={"Origin": "https://evil.example"})
            acao = r.headers.get("access-control-allow-origin", "")
            acac = r.headers.get("access-control-allow-credentials", "")
            if acao == "https://evil.example" and acac.lower() == "true":
                self.add_finding("CORS_CREDENTIALS_RISK", "HIGH", "Credentialed CORS trust risk", self.target,
                                 "Server reflected arbitrary Origin with credentials enabled.", 90,
                                 "Attackers may read authenticated responses from a malicious origin.",
                                 "Use a strict allowlist and avoid credentials on wildcard/reflected origins.")
        except Exception:
            pass
        missing = []
        for h in ["content-security-policy", "x-frame-options", "x-content-type-options", "referrer-policy"]:
            # headers not stored in observation, so refetch root once
            pass
        try:
            r = self.session.get(self.target, timeout=self.timeout)
            for h in ["content-security-policy", "x-frame-options", "x-content-type-options", "referrer-policy"]:
                if h not in {k.lower(): v for k, v in r.headers.items()}:
                    missing.append(h)
            if len(missing) >= 2:
                self.add_finding("MISSING_SECURITY_HEADERS", "LOW", "Missing security headers", self.target,
                                 "Missing: " + ", ".join(missing), 42,
                                 "Missing headers increase exploit impact but are usually not standalone critical issues.",
                                 "Add CSP, frame protection, nosniff, and referrer policy.", false_positive_risk="LOW")
        except Exception:
            pass

    def run_access_matrix(self, user_ctx: Optional[AuthContext] = None, admin_ctx: Optional[AuthContext] = None) -> List[Dict[str, Any]]:
        matrix: List[Dict[str, Any]] = []
        candidates = sorted(set(self.sitemap.admin_candidates + self.sitemap.graphql_candidates + [u for u in self.sitemap.endpoints if "/api/" in urlparse(u).path]))[:80]
        public = AuthContext(name="public")
        for url in candidates:
            public_obs, public_body = self.fetch(url, public)
            row: Dict[str, Any] = {"url": url, "public": public_obs.status}
            user_obs = None
            if user_ctx:
                user_obs, user_body = self.fetch(url, user_ctx)
                row["user"] = user_obs.status
                if public_obs.status in {401, 403} and user_obs.status == 200 and any(word in urlparse(url).path.lower() for word in ADMIN_WORDS):
                    self.add_finding("BROKEN_ADMIN_ACCESS_CONTROL", "CRITICAL", "User context reached admin/internal endpoint", url,
                                     f"public={public_obs.status}, user={user_obs.status}, body_hash={user_obs.body_hash}", 96,
                                     "A non-admin user may reach admin-level data/actions, enabling data theft or fraud.",
                                     "Enforce server-side role checks on every admin/internal endpoint.")
            if admin_ctx:
                admin_obs, _ = self.fetch(url, admin_ctx)
                row["admin"] = admin_obs.status
            if public_obs.status == 200 and any(word in urlparse(url).path.lower() for word in ADMIN_WORDS):
                self.add_finding("PUBLIC_ADMIN_ENDPOINT", "HIGH", "Admin/internal endpoint reachable publicly", url,
                                 f"public HTTP {public_obs.status}", 88,
                                 "Public access to admin/internal routes can expose data or operational controls.",
                                 "Require authentication and authorization before returning admin data.")
            matrix.append(row)
        return matrix

    def analyze_tokens(self, ctx: Optional[AuthContext]) -> None:
        if not ctx:
            return
        values = []
        for v in ctx.headers.values():
            values.extend(JWT_RE.findall(str(v)))
        for v in ctx.cookies.values():
            values.extend(JWT_RE.findall(str(v)))
        for token in values[:5]:
            parts = token.split(".")
            try:
                header = json.loads(base64.urlsafe_b64decode(parts[0] + "=" * (-len(parts[0]) % 4)))
                payload = json.loads(base64.urlsafe_b64decode(parts[1] + "=" * (-len(parts[1]) % 4)))
            except Exception:
                continue
            warnings = []
            if str(header.get("alg", "")).lower() == "none":
                warnings.append("alg=none")
            if "exp" not in payload:
                warnings.append("missing exp")
            for claim in ["role", "isAdmin", "admin", "permissions", "orgId", "userId"]:
                if claim in payload:
                    warnings.append(f"authorization-related claim: {claim}")
            if warnings:
                self.add_finding("JWT_AUTHZ_REVIEW", "MEDIUM", "JWT authorization claims need review", "provided auth context",
                                 "; ".join(warnings), 65,
                                 "Weak or client-trusted token claims can cause privilege boundary mistakes.",
                                 "Validate JWT signature, issuer, audience, expiration, and enforce authorization server-side.", false_positive_risk="MEDIUM")

    def add_finding(self, type_: str, severity: str, title: str, location: str, evidence: str, confidence: int, impact: str, remediation: str, false_positive_risk: str = "LOW") -> None:
        attacker_value = impact_to_attacker_value(type_, impact)
        self.findings.append(Finding(type_, severity, title, location, redacted(evidence), confidence, impact, remediation, false_positive_risk=false_positive_risk, attacker_value=attacker_value, proof={"generated_at": now_iso()}))

    def run(self, user_ctx: Optional[AuthContext] = None, admin_ctx: Optional[AuthContext] = None) -> Dict[str, Any]:
        self.crawl()
        self.run_exposure_checks()
        self.run_js_intelligence()
        self.run_header_and_cors_checks()
        self.analyze_tokens(user_ctx)
        access_matrix = self.run_access_matrix(user_ctx=user_ctx, admin_ctx=admin_ctx)
        return {
            "target": self.target,
            "timestamp": now_iso(),
            "site_map": asdict(self.sitemap),
            "access_matrix": access_matrix,
            "findings": [f.to_dict() for f in sorted(self.findings, key=lambda x: (x.confidence, severity_rank(x.severity)), reverse=True)],
            "summary": summarize_findings(self.findings),
        }


def severity_rank(sev: str) -> int:
    return {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}.get(sev.upper(), 0)


def impact_to_attacker_value(type_: str, impact: str) -> str:
    t = type_.upper()
    if "ACCESS" in t or "ADMIN" in t:
        return "Potential account takeover, fraud, user data theft, or internal data exposure."
    if "CONFIG" in t or "SECRET" in t:
        return "Potential API abuse, cloud abuse, payment abuse, or downstream system access."
    if "WEB3" in t:
        return "Potential wallet/signature abuse risk if transaction logic is unsafe."
    if "CORS" in t:
        return "Potential authenticated data read from malicious origin."
    if "GRAPHQL" in t or "API" in t:
        return "Potential endpoint enumeration, data exposure, or weak resolver abuse."
    return impact


def summarize_findings(findings: Iterable[Finding]) -> Dict[str, Any]:
    counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
    high_confidence = 0
    for f in findings:
        counts[f.severity] = counts.get(f.severity, 0) + 1
        if f.confidence >= 80:
            high_confidence += 1
    return {"counts": counts, "total": sum(counts.values()), "high_confidence": high_confidence}


def write_reports(result: Dict[str, Any], output_dir: str = "output/fox_site_intelligence") -> Dict[str, str]:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    json_path = out / "fox_report.json"
    md_path = out / "fox_report.md"
    html_path = out / "fox_report.html"
    endpoints_path = out / "interesting_endpoints.txt"
    admin_path = out / "admin_surface.txt"

    json_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    site_map = result.get("site_map", {})
    endpoints_path.write_text("\n".join(site_map.get("endpoints", [])), encoding="utf-8")
    admin_path.write_text("\n".join(site_map.get("admin_candidates", [])), encoding="utf-8")

    lines = [f"# Fox Site Intelligence Report", "", f"Target: `{result.get('target')}`", f"Generated: `{result.get('timestamp')}`", "", "## Summary", "", "```json", json.dumps(result.get("summary", {}), indent=2), "```", "", "## Findings", ""]
    for f in result.get("findings", []):
        lines.extend([
            f"### {f['severity']} - {f['title']}", "",
            f"- Type: `{f['type']}`",
            f"- Location: `{f['location']}`",
            f"- Confidence: `{f['confidence']}%`",
            f"- False-positive risk: `{f['false_positive_risk']}`",
            f"- Evidence: `{f['evidence']}`",
            f"- Attacker value: {f['attacker_value']}",
            f"- Impact: {f['impact']}",
            f"- Fix: {f['remediation']}", "",
        ])
    md_path.write_text("\n".join(lines), encoding="utf-8")
    html_body = "<html><body><pre>" + md_path.read_text(encoding="utf-8").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;") + "</pre></body></html>"
    html_path.write_text(html_body, encoding="utf-8")
    return {"json": str(json_path), "markdown": str(md_path), "html": str(html_path), "endpoints": str(endpoints_path), "admin_surface": str(admin_path)}
