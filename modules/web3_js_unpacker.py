#!/usr/bin/env python3
from __future__ import annotations

import base64
import codecs
import json
import re
from typing import Dict, List

BASE64_RE = re.compile(r"(?<![A-Za-z0-9+/=])([A-Za-z0-9+/]{24,}={0,2})(?![A-Za-z0-9+/=])")
HEX_RE = re.compile(r"0x([0-9a-fA-F]{16,})")
UNICODE_ESCAPE_RE = re.compile(r"(?:\\u[0-9a-fA-F]{4}){3,}")
ROUTE_RE = re.compile(r"['\"](/[A-Za-z0-9_./?=&%:-]{2,120})['\"]")
ENV_RE = re.compile(r"\b(?:NEXT_PUBLIC_|VITE_|REACT_APP_|PUBLIC_)[A-Z0-9_]{3,}\b")


def _try_b64(value: str) -> str | None:
    try:
        padded = value + "=" * ((4 - len(value) % 4) % 4)
        decoded = base64.b64decode(padded, validate=False)
        text = decoded.decode("utf-8", errors="ignore")
        if len(text) >= 8 and sum(ch.isprintable() for ch in text) / max(len(text), 1) > 0.8:
            return text
    except Exception:
        return None
    return None


def _try_hex(value: str) -> str | None:
    try:
        decoded = bytes.fromhex(value).decode("utf-8", errors="ignore")
        if len(decoded) >= 8 and sum(ch.isprintable() for ch in decoded) / max(len(decoded), 1) > 0.8:
            return decoded
    except Exception:
        return None
    return None


def unpack_js_text(text: str, max_items: int = 250) -> Dict[str, List[str]]:
    decoded_strings: List[str] = []
    for match in BASE64_RE.findall(text):
        decoded = _try_b64(match)
        if decoded and decoded not in decoded_strings:
            decoded_strings.append(decoded[:2000])
        if len(decoded_strings) >= max_items:
            break

    for match in HEX_RE.findall(text):
        decoded = _try_hex(match)
        if decoded and decoded not in decoded_strings:
            decoded_strings.append(decoded[:2000])
        if len(decoded_strings) >= max_items:
            break

    for match in UNICODE_ESCAPE_RE.findall(text):
        try:
            decoded = codecs.decode(match, "unicode_escape")
            if decoded and decoded not in decoded_strings:
                decoded_strings.append(decoded[:2000])
        except Exception:
            pass
        if len(decoded_strings) >= max_items:
            break

    routes = sorted(set(ROUTE_RE.findall(text)))[:max_items]
    env_names = sorted(set(ENV_RE.findall(text)))[:max_items]

    json_blobs: List[str] = []
    for raw in re.findall(r"\{[^{}]{20,1000}\}", text):
        try:
            obj = json.loads(raw)
            if isinstance(obj, dict):
                json_blobs.append(json.dumps(obj)[:2000])
        except Exception:
            continue
        if len(json_blobs) >= max_items:
            break

    return {
        "decoded_strings": decoded_strings,
        "routes": routes,
        "env_names": env_names,
        "json_blobs": json_blobs,
    }


def enrich_site_data_with_unpacked_js(site_data: Dict, max_items: int = 250) -> Dict:
    extra_items = []
    for item in site_data.get("js_analysis", {}).get("js_content", []) or []:
        if not isinstance(item, dict):
            continue
        url = str(item.get("url", "js"))
        content = str(item.get("content", ""))
        unpacked = unpack_js_text(content, max_items=max_items)
        combined = "\n".join(unpacked["decoded_strings"] + unpacked["routes"] + unpacked["env_names"] + unpacked["json_blobs"])
        if combined.strip():
            extra_items.append({"url": f"unpacked::{url}", "content": combined})
    site_data.setdefault("js_analysis", {}).setdefault("js_content", []).extend(extra_items)
    site_data["unpacked_js"] = {"items_added": len(extra_items)}
    return site_data
