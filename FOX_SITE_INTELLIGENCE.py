#!/usr/bin/env python3
"""
FOX_SITE_INTELLIGENCE.py

All-in-one application intelligence scanner for authorized testing:
- site mapping
- JS/API/admin route extraction
- Web3/Solana markers
- exposure checks
- auth/access matrix with provided sessions
- proof scoring and attacker-value impact report
"""

from __future__ import annotations

import argparse
import json
import sys

from modules.fox_site_intelligence import AuthContext, FoxSiteIntelligence, write_reports


def main() -> None:
    parser = argparse.ArgumentParser(description="Fox Site Intelligence - deep weakness and app intelligence scanner")
    parser.add_argument("--target", "-t", required=True, help="Target URL")
    parser.add_argument("--deep", action="store_true", help="Follow same-origin links for deeper mapping")
    parser.add_argument("--browser", action="store_true", help="Reserved for future Playwright runtime capture")
    parser.add_argument("--web3", action="store_true", help="Emphasize Web3/Solana findings in report")
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
    reports = write_reports(result, args.output)
    result["reports"] = reports

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
