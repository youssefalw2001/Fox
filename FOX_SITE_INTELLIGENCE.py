#!/usr/bin/env python3
"""
FOX_SITE_INTELLIGENCE.py

All-in-one application intelligence scanner for authorized testing:
- site mapping
- JS/API/admin route extraction
- Web3/Solana markers
- exposure checks
- data exposure intelligence
- auth/access matrix with provided sessions
- proof scoring and attacker-value impact report
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from modules.data_exposure_intel import build_data_exposure_report
from modules.fox_site_intelligence import AuthContext, FoxSiteIntelligence, write_reports


def collect_data_intel_blobs(scanner: FoxSiteIntelligence) -> tuple[dict, dict]:
    """Collect proof-sized response bodies for safe exposure classification."""
    blobs = {}
    content_types = {}

    for url, text in scanner.sitemap.js_blobs.items():
        blobs[url] = text
        content_types[url] = "application/javascript"

    for page in scanner.sitemap.pages:
        obs, text = scanner.fetch(page.url)
        if text:
            blobs[page.url] = text[:1_000_000]
            content_types[page.url] = obs.content_type

    # Pull obvious source maps referenced by JS URLs without broad crawling.
    for js_url in list(scanner.sitemap.scripts)[:40]:
        map_url = js_url + ".map"
        obs, text = scanner.fetch(map_url)
        if obs.status == 200 and text:
            blobs[map_url] = text[:1_000_000]
            content_types[map_url] = obs.content_type or "application/json"

    return blobs, content_types


def main() -> None:
    parser = argparse.ArgumentParser(description="Fox Site Intelligence - deep weakness and app intelligence scanner")
    parser.add_argument("--target", "-t", required=True, help="Target URL")
    parser.add_argument("--deep", action="store_true", help="Follow same-origin links for deeper mapping")
    parser.add_argument("--browser", action="store_true", help="Reserved for future Playwright runtime capture")
    parser.add_argument("--web3", action="store_true", help="Emphasize Web3/Solana findings in report")
    parser.add_argument("--data-intel", action="store_true", help="Run deep data exposure intelligence with redacted proof")
    parser.add_argument("--headers", help="JSON file with normal-user headers")
    parser.add_argument("--cookies", help="JSON file with normal-user cookies")
    parser.add_argument("--admin-headers", help="JSON file with authorized admin headers for comparison")
    parser.add_argument("--admin-cookies", help="JSON file with authorized admin cookies for comparison")
    parser.add_argument("--timeout", type=int, default=8, help="HTTP timeout")
    parser.add_argument("--max-pages", type=int, default=60, help="Maximum pages/endpoints to map")
    parser.add_argument("--output", "-o", default="output/fox_site_intelligence", help="Output directory")
    parser.add_argument("--print-json", action="store_true", help="Print full JSON result to stdout")
    args = parser.parse_args()

    user_ctx = None
    admin_ctx = None
    if args.headers or args.cookies:
        user_ctx = AuthContext.from_files(args.headers, args.cookies, name="user")
    if args.admin_headers or args.admin_cookies:
        admin_ctx = AuthContext.from_files(args.admin_headers, args.admin_cookies, name="admin")

    scanner = FoxSiteIntelligence(args.target, timeout=args.timeout, max_pages=args.max_pages, deep=args.deep)
    result = scanner.run(user_ctx=user_ctx, admin_ctx=admin_ctx)

    if args.data_intel:
        blobs, content_types = collect_data_intel_blobs(scanner)
        data_exposure = build_data_exposure_report(blobs, content_types)
        result["data_exposure"] = data_exposure
        for exposure in data_exposure.get("findings", [])[:50]:
            scanner.add_finding(
                exposure.get("type", "DATA_EXPOSURE"),
                exposure.get("severity", "MEDIUM"),
                f"Data exposure intelligence: {exposure.get('type', 'signal')}",
                exposure.get("location", "unknown"),
                exposure.get("evidence", ""),
                int(exposure.get("confidence", 60)),
                exposure.get("attacker_value", "Sensitive exposure may support fraud, account abuse, or infrastructure abuse."),
                exposure.get("remediation", "Remove exposed sensitive data and restrict access."),
                false_positive_risk="MEDIUM" if exposure.get("confidence", 0) < 85 else "LOW",
            )
        result["findings"] = [f.to_dict() for f in sorted(scanner.findings, key=lambda x: (x.confidence, x.severity), reverse=True)]
        result["summary"] = result["summary"] | {"data_exposure": data_exposure.get("summary", {})}

    reports = write_reports(result, args.output)
    result["reports"] = reports

    if args.data_intel:
        out = Path(args.output)
        out.mkdir(parents=True, exist_ok=True)
        data_path = out / "data_exposure.json"
        data_path.write_text(json.dumps(result.get("data_exposure", {}), indent=2), encoding="utf-8")
        reports["data_exposure"] = str(data_path)

    print("\n" + "=" * 70)
    print("FOX SITE INTELLIGENCE COMPLETE")
    print("=" * 70)
    print(f"Target: {result['target']}")
    print(f"Findings: {result['summary']['total']}")
    print(f"High confidence: {result['summary']['high_confidence']}")
    print(f"JSON: {reports['json']}")
    print(f"Markdown: {reports['markdown']}")
    print(f"HTML: {reports['html']}")
    print(f"Endpoints: {reports['endpoints']}")
    print(f"Admin surface: {reports['admin_surface']}")
    if args.data_intel:
        print(f"Data exposure: {reports['data_exposure']}")

    if result.get("findings"):
        print("\nTop findings:")
        for f in result["findings"][:10]:
            print(f"  {f['severity']:8s} {f['confidence']:3d}%  {f['type']:30s} {f['location']}")

    if args.browser:
        print("\n[Note] --browser flag is accepted for workflow compatibility; Playwright runtime capture can be added next.")
    if args.web3:
        print("[Note] --web3 flag is accepted; Web3 markers are already extracted from JS/frontend content.")

    if args.print_json:
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[!] Interrupted")
        sys.exit(130)
