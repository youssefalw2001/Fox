#!/usr/bin/env python3
from __future__ import annotations

import re
from typing import Dict, List
from urllib.parse import urlparse

API_KIND_RULES = [
    ("quote", ["quote", "price", "route"]),
    ("swap", ["swap", "transaction", "tx", "execute"]),
    ("auth", ["auth", "login", "session", "jwt", "token"]),
    ("wallet", ["wallet", "phantom", "solana"]),
    ("rpc", ["rpc", "graphql", "query"]),
    ("asset", ["token", "mint", "pool", "market"]),
]

METHOD_HINTS = {
    "GET": re.compile(r"\bfetch\s*\(\s*['\"]([^'\"]+)['\"]", re.I),
    "POST": re.compile(r"method\s*:\s*['\"]POST['\"]", re.I),
}


def classify_api_url(url: str) -> Dict[str, object]:
    low = url.lower()
    kinds: List[str] = []
    for kind, terms in API_KIND_RULES:
        if any(term in low for term in terms):
            kinds.append(kind)
    parsed = urlparse(url)
    return {
        "url": url,
        "path": parsed.path,
        "kinds": sorted(set(kinds)) or ["unknown"],
        "has_query": bool(parsed.query),
    }


def map_apis(site_data: Dict) -> Dict[str, object]:
    api_urls = set(site_data.get("api_analysis", {}).get("api_urls", []) or [])
    for item in site_data.get("api_analysis", {}).get("api_content", []) or []:
        if isinstance(item, dict) and item.get("url"):
            api_urls.add(str(item["url"]))

    mapped = [classify_api_url(url) for url in sorted(api_urls)]
    counts: Dict[str, int] = {}
    for item in mapped:
        for kind in item["kinds"]:
            counts[kind] = counts.get(kind, 0) + 1

    return {
        "total": len(mapped),
        "by_kind": counts,
        "endpoints": mapped,
    }
