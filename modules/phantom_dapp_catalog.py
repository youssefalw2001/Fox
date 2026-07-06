#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set
from urllib.parse import urljoin, urlparse

import requests

PHANTOM_MARKERS = {
    "isPhantom": 35,
    "window.solana": 30,
    "PhantomProvider": 25,
    "phantom.app": 18,
    "connect Phantom": 22,
    "connect wallet": 16,
    "@solana/wallet-adapter": 25,
    "wallet-adapter-react": 22,
    "solanaWeb3": 20,
    "mainnet-beta": 16,
    "api.mainnet-beta.solana.com": 16,
}

TOPIC_MARKERS = {
    "defi": 10,
    "swap": 10,
    "staking": 10,
    "stake": 7,
    "vault": 8,
    "yield": 8,
    "liquidity": 7,
    "nft": 8,
    "mint": 8,
    "claim": 7,
    "airdrop": 7,
    "gamefi": 9,
    "casino": 8,
    "bet": 6,
    "prediction": 6,
}

LARGE_BRAND_BLOCKLIST = {
    "binance", "coinbase", "kraken", "okx", "bybit", "kucoin", "crypto.com",
    "jupiter", "raydium", "magiceden", "phantom.app", "solana.com", "helius",
    "quicknode", "alchemy", "moralis", "opensea", "metaplex", "ledger", "trezor",
    "backpack", "drift", "tensor", "marinade", "orca.so",
}

STATIC_EXTENSIONS = (
    ".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".ico", ".css",
    ".woff", ".woff2", ".ttf", ".pdf", ".zip", ".gz", ".tar", ".mp4",
)

URL_RE = re.compile(r"https?://[^\s\"'<>]+", re.I)
HREF_RE = re.compile(r"(?:href|src)=[\"']([^\"']+)[\"']", re.I)
SCRIPT_RE = re.compile(r"<script[^>]+src=[\"']([^\"']+\.js[^\"']*)[\"']", re.I)


@dataclass
class DappScore:
    url: str
    domain: str
    score: int
    verdict: str
    matched_markers: Dict[str, int]
    reasons: List[str]
    first_seen: str
    fresh: bool
    skipped: bool = False
    skip_reason: Optional[str] = None

    def to_dict(self) -> Dict:
        return asdict(self)


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def normalize_url(value: str) -> Optional[str]:
    value = (value or "").strip().strip("'\"")
    if not value:
        return None
    if value.startswith("//"):
        value = "https:" + value
    if not value.startswith(("http://", "https://")):
        value = "https://" + value
    parsed = urlparse(value)
    if not parsed.netloc:
        return None
    if parsed.path.lower().endswith(STATIC_EXTENSIONS):
        return None
    clean_path = parsed.path or ""
    return f"{parsed.scheme}://{parsed.netloc}{clean_path}".rstrip("/")


def domain_of(url: str) -> str:
    return urlparse(url).netloc.lower().removeprefix("www.")


def load_seen(path: str) -> Dict[str, Dict]:
    p = Path(path)
    if not p.exists():
        return {}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def save_seen(path: str, seen: Dict[str, Dict]) -> None:
    Path(path).write_text(json.dumps(seen, indent=2, sort_keys=True), encoding="utf-8")


def read_candidates(path: str) -> List[str]:
    values: List[str] = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        normalized = normalize_url(line)
        if normalized:
            values.append(normalized)
    return values


def extract_urls(text: str, base_url: Optional[str] = None, limit: int = 300) -> List[str]:
    found: Set[str] = set()
    for match in URL_RE.findall(text or ""):
        normalized = normalize_url(match.rstrip(").,;]"))
        if normalized:
            found.add(normalized)
    if base_url:
        for raw in HREF_RE.findall(text or ""):
            normalized = normalize_url(urljoin(base_url, raw))
            if normalized:
                found.add(normalized)
    return sorted(found)[:limit]


def fetch_text(url: str, timeout: int = 8, max_bytes: int = 500_000) -> str:
    try:
        r = requests.get(
            url,
            timeout=timeout,
            allow_redirects=True,
            headers={"User-Agent": "FoxPhantomDappCatalog/1.0"},
        )
        return r.content[:max_bytes].decode(r.encoding or "utf-8", errors="ignore")
    except Exception:
        return ""


def expand_from_seed_pages(seed_urls: Iterable[str], timeout: int = 8, limit_per_seed: int = 200) -> List[str]:
    urls: Set[str] = set()
    for seed in seed_urls:
        seed = normalize_url(seed) or ""
        if not seed:
            continue
        text = fetch_text(seed, timeout=timeout)
        for url in extract_urls(text, base_url=seed, limit=limit_per_seed):
            urls.add(url)
    return sorted(urls)


def collect_homepage_and_scripts(url: str, timeout: int = 8, max_scripts: int = 8) -> str:
    html = fetch_text(url, timeout=timeout)
    chunks = [html]
    for src in SCRIPT_RE.findall(html)[:max_scripts]:
        js_url = urljoin(url, src)
        if domain_of(js_url) == domain_of(url):
            chunks.append(fetch_text(js_url, timeout=timeout, max_bytes=300_000))
    return "\n".join(chunks)


def blocked_brand(domain: str) -> Optional[str]:
    for brand in LARGE_BRAND_BLOCKLIST:
        if brand in domain:
            return brand
    return None


def score_dapp(url: str, seen: Dict[str, Dict], timeout: int = 8) -> DappScore:
    normalized = normalize_url(url) or url
    domain = domain_of(normalized)
    first_seen = seen.get(domain, {}).get("first_seen", now_iso())
    fresh = domain not in seen

    brand = blocked_brand(domain)
    if brand:
        return DappScore(normalized, domain, -100, "SKIP_LARGE_BRAND", {}, [], first_seen, fresh, True, f"large brand: {brand}")

    text = collect_homepage_and_scripts(normalized, timeout=timeout)
    low = text.lower()
    score = 0
    matched: Dict[str, int] = {}
    reasons: List[str] = []

    for marker, points in PHANTOM_MARKERS.items():
        if marker.lower() in low:
            score += points
            matched[marker] = points
            reasons.append(f"Phantom/Solana marker: {marker}")

    for marker, points in TOPIC_MARKERS.items():
        if marker.lower() in low or marker.lower() in domain:
            score += points
            matched[marker] = matched.get(marker, 0) + points
            reasons.append(f"dApp topic marker: {marker}")

    if fresh:
        score += 12
        reasons.append("fresh domain not seen before")
    else:
        score -= 30
        reasons.append("already seen before")

    if domain.endswith((".xyz", ".app", ".io", ".finance", ".game", ".bet", ".fun")):
        score += 5
        reasons.append("startup-style TLD")

    if len(text) < 250:
        score -= 20
        reasons.append("thin/unreachable page")

    if score >= 75:
        verdict = "EXCELLENT_PHANTOM_DAPP"
    elif score >= 50:
        verdict = "GOOD_PHANTOM_DAPP"
    elif score >= 30:
        verdict = "POSSIBLE_PHANTOM_DAPP"
    else:
        verdict = "LOW_PRIORITY"

    return DappScore(normalized, domain, score, verdict, matched, reasons[:20], first_seen, fresh)


def rank_dapps(urls: Iterable[str], seen_path: str, timeout: int = 8, min_score: int = 30, fresh_only: bool = True) -> List[DappScore]:
    seen = load_seen(seen_path)
    results: List[DappScore] = []
    checked: Set[str] = set()
    for raw in urls:
        normalized = normalize_url(raw)
        if not normalized:
            continue
        domain = domain_of(normalized)
        if domain in checked:
            continue
        checked.add(domain)
        item = score_dapp(normalized, seen=seen, timeout=timeout)
        if item.skipped:
            continue
        if fresh_only and not item.fresh:
            continue
        if item.score >= min_score:
            results.append(item)
            seen.setdefault(item.domain, {"first_seen": item.first_seen})
            seen[item.domain].update({"last_seen": now_iso(), "last_score": item.score, "last_url": item.url})
    save_seen(seen_path, seen)
    return sorted(results, key=lambda x: x.score, reverse=True)


def write_outputs(results: List[DappScore], text_output: str, json_output: str) -> None:
    Path(text_output).write_text("\n".join(item.url for item in results) + ("\n" if results else ""), encoding="utf-8")
    Path(json_output).write_text(json.dumps([item.to_dict() for item in results], indent=2), encoding="utf-8")
