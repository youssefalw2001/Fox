#!/usr/bin/env python3
from __future__ import annotations

import re
from typing import Dict, List, Optional, Set
from urllib.parse import urljoin, urlparse, urlunparse

import requests

BASE58_RE = r"[1-9A-HJ-NP-Za-km-z]"
SOLANA_ADDRESS_RE = re.compile(rf"\b{BASE58_RE}{{32,44}}\b")
URL_RE = re.compile(r"(?:https?|wss?)://[^\"'\s<>\\)]+", re.I)
SCRIPT_SRC_RE = re.compile(r"<script[^>]+src=[\"']([^\"']+)[\"']", re.I)
LINK_HREF_RE = re.compile(r"<(?:a|link)[^>]+href=[\"']([^\"']+)[\"']", re.I)
SOURCE_MAP_RE = re.compile(r"//#\s*sourceMappingURL=([^\s]+)", re.I)
API_PATH_RE = re.compile(r"[\"']((?:/api/|/v\d+/|/rpc/|/graphql|/quote|/swap|/transaction|/tokens|/wallet|/auth)[^\"'\s<>]*)[\"']", re.I)
NEXT_BUILD_RE = re.compile(r"/_next/static/([^/]+)/")
VITE_ASSET_RE = re.compile(r"/assets/[^\"'\s<>]+\.(?:js|mjs|map)", re.I)
ROUTE_RE = re.compile(r"[\"'](/[A-Za-z0-9_./?=&%:-]{2,120})[\"']")


class Web3AssetCollector:
    def __init__(self, timeout: int = 10, debug: bool = False, max_routes: int = 40, max_files: int = 80, browser: bool = False):
        self.timeout = timeout
        self.debug = debug
        self.max_routes = max_routes
        self.max_files = max_files
        self.browser = browser
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "Mozilla/5.0 (compatible; FoxAssetCollector/1.0)"})

    def _log(self, msg: str) -> None:
        if self.debug:
            print(f"    [assets] {msg}")

    def _get(self, url: str, timeout: Optional[int] = None) -> Optional[requests.Response]:
        try:
            return self.session.get(url, timeout=timeout or self.timeout, allow_redirects=True)
        except requests.RequestException as exc:
            self._log(f"request failed {url}: {exc}")
            return None

    def _text(self, response: Optional[requests.Response]) -> str:
        if response is None:
            return ""
        try:
            return response.text or ""
        except Exception:
            return ""

    def _norm(self, base: str, raw: str) -> Optional[str]:
        if not raw or raw.startswith(("mailto:", "tel:", "javascript:", "data:", "#", "//")):
            return None
        url = urljoin(base, raw)
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https") or not parsed.netloc:
            return None
        return urlunparse(parsed._replace(fragment=""))

    def _same_origin(self, base: str, candidate: str) -> bool:
        b = urlparse(base)
        c = urlparse(candidate)
        return (b.scheme, b.netloc) == (c.scheme, c.netloc)

    def _score(self, url: str) -> int:
        low = url.lower()
        if any(x in low for x in (".js", ".mjs", ".map", "_next/static", "/assets/")):
            return 0
        if any(x in low for x in ("/api/", "/graphql", "/rpc/", "/quote", "/swap", "/transaction")):
            return 1
        return 2

    def _extract_urls(self, base: str, text: str) -> Set[str]:
        raw_items: List[str] = []
        raw_items.extend(SCRIPT_SRC_RE.findall(text))
        raw_items.extend(LINK_HREF_RE.findall(text))
        raw_items.extend(API_PATH_RE.findall(text))
        raw_items.extend(ROUTE_RE.findall(text))
        raw_items.extend(VITE_ASSET_RE.findall(text))
        for build_id in NEXT_BUILD_RE.findall(text)[:3]:
            raw_items.extend([
                f"/_next/static/{build_id}/_buildManifest.js",
                f"/_next/static/{build_id}/_ssgManifest.js",
                f"/_next/static/{build_id}/_middlewareManifest.js",
            ])
        out: Set[str] = set()
        for raw in raw_items:
            url = self._norm(base, raw)
            if url and self._same_origin(base, url):
                out.add(url)
        return out

    def _sitemap_robots(self, target: str) -> Set[str]:
        out: Set[str] = set()
        for path in ("/sitemap.xml", "/robots.txt"):
            url = self._norm(target, path)
            if not url:
                continue
            res = self._get(url, timeout=min(self.timeout, 6))
            text = self._text(res)
            if path.endswith("robots.txt"):
                matches = re.findall(r"(?im)^\s*(?:allow|disallow):\s*(/[^\s#]+)", text)
            else:
                matches = re.findall(r"<loc>(.*?)</loc>", text, re.I)
            for raw in matches:
                found = self._norm(target, raw.strip())
                if found and self._same_origin(target, found):
                    out.add(found)
        return out

    def _browser_collect(self, target: str) -> Dict:
        result = {"enabled": False, "ok": False, "page_text": "", "network_urls": [], "error": None}
        if not self.browser:
            return result
        result["enabled"] = True
        try:
            from playwright.sync_api import sync_playwright
        except Exception as exc:
            result["error"] = f"playwright unavailable: {exc}"
            self._log(str(result["error"]))
            return result
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                seen: List[str] = []
                page.on("request", lambda req: seen.append(req.url))
                page.goto(target, wait_until="networkidle", timeout=max(10000, self.timeout * 1000))
                result["page_text"] = page.content()
                result["network_urls"] = sorted(set(seen))[:300]
                result["ok"] = True
                browser.close()
        except Exception as exc:
            result["error"] = f"render failed: {type(exc).__name__}: {exc}"
            self._log(str(result["error"]))
        return result

    def collect(self, target: str) -> Dict:
        home_res = self._get(target)
        home = self._text(home_res)
        browser_data = self._browser_collect(target)
        rendered = str(browser_data.get("page_text") or "")
        seed = home + "\n" + rendered

        discovered: Set[str] = set()
        discovered.update(self._extract_urls(target, seed))
        discovered.update(self._sitemap_robots(target))
        for u in browser_data.get("network_urls", []) or []:
            n = self._norm(target, str(u))
            if n and self._same_origin(target, n):
                discovered.add(n)

        todo = sorted(discovered, key=self._score)[: self.max_routes]
        route_items: List[Dict[str, str]] = []
        file_items: List[Dict[str, str]] = []
        api_items: List[Dict[str, str]] = []
        second: Set[str] = set()

        for url in todo:
            res = self._get(url, timeout=min(self.timeout, 8))
            if not res or res.status_code >= 500:
                continue
            text = self._text(res)
            ctype = (res.headers.get("content-type") or "").lower()
            path = urlparse(url).path.lower()
            is_file = any(path.endswith(ext) for ext in (".js", ".mjs", ".map")) or "javascript" in ctype or "json" in ctype
            is_api = any(x in path for x in ("/api/", "/graphql", "/rpc/", "/quote", "/swap", "/transaction", "/auth"))
            if is_file and len(file_items) < self.max_files and len(text) <= 3_000_000:
                file_items.append({"url": url, "content": text})
                for sm in SOURCE_MAP_RE.findall(text):
                    n = self._norm(url, sm.strip())
                    if n and self._same_origin(target, n):
                        second.add(n)
                second.update(self._extract_urls(url, text))
            elif is_api and len(text) <= 1_500_000:
                api_items.append({"url": url, "content": text[:1_500_000]})
            elif len(text) <= 1_500_000:
                route_items.append({"url": url, "content": text[:1_500_000]})
                second.update(self._extract_urls(url, text))

        for url in sorted(second, key=self._score):
            if len(file_items) >= self.max_files or url in todo:
                continue
            path = urlparse(url).path.lower()
            if not any(x in path for x in (".js", ".mjs", ".map", "_buildmanifest", "_ssgmanifest")):
                continue
            res = self._get(url, timeout=min(self.timeout, 8))
            if res and res.status_code < 400:
                text = self._text(res)
                if len(text) <= 3_000_000:
                    file_items.append({"url": url, "content": text})

        combined = seed + "\n" + "\n".join(x["content"] for x in route_items + file_items + api_items)
        rpc_urls = sorted(set(u for u in URL_RE.findall(combined) if any(k in u.lower() for k in ("solana", "rpc", "helius", "quicknode", "alchemy", "mainnet", "devnet", "jupiter", "raydium"))))
        program_ids = sorted(set(SOLANA_ADDRESS_RE.findall(combined)))
        api_urls = sorted(set(n for n in (self._norm(target, raw) for raw in API_PATH_RE.findall(combined)) if n and self._same_origin(target, n)))

        scanner_items = list(file_items)
        scanner_items.extend(route_items)
        scanner_items.extend(api_items)
        if rendered:
            scanner_items.append({"url": "browser-rendered-dom", "content": rendered})

        return {
            "page_text": home,
            "rendered_text": rendered,
            "page_status": home_res.status_code if home_res else None,
            "browser": browser_data,
            "routes": route_items,
            "discovered_routes": todo,
            "js_analysis": {
                "program_ids": program_ids,
                "rpc_urls": rpc_urls,
                "js_content": scanner_items,
                "js_urls": [x["url"] for x in file_items],
            },
            "api_analysis": {
                "api_urls": api_urls,
                "api_content": api_items,
            },
            "coverage": {
                "routes_fetched": len(route_items),
                "files_fetched": len(file_items),
                "api_responses_fetched": len(api_items),
                "program_ids": len(program_ids),
                "rpc_urls": len(rpc_urls),
                "api_urls": len(api_urls),
                "browser_enabled": bool(browser_data.get("enabled")),
                "browser_ok": bool(browser_data.get("ok")),
            },
        }


def collect_web3_assets(target: str, timeout: int = 10, debug: bool = False, max_routes: int = 40, max_files: int = 80, browser: bool = False) -> Dict:
    return Web3AssetCollector(timeout=timeout, debug=debug, max_routes=max_routes, max_files=max_files, browser=browser).collect(target)
