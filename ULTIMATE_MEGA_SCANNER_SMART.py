#!/usr/bin/env python3
"""
Smart accuracy runner for ULTIMATE_MEGA_SCANNER.py.

This keeps the original scanner logic unchanged, then post-processes results with:
- duplicate finding removal
- confidence scoring
- noisy finding warnings
- evidence redaction in reports
- smarter JSON/HTML/Markdown report output through the original reporter
"""

from __future__ import annotations

import argparse
import sys
import time

import ULTIMATE_MEGA_SCANNER as ums
from modules.mega_accuracy_enhancer import enhance_scan_results


class SmartUltimateMegaScanner(ums.UltimateMegaScanner):
    def scan(self, target: str):
        results = super().scan(target)
        enhanced = enhance_scan_results(results)
        self.scan_results = enhanced

        print("\n" + "=" * 70)
        print(ums.Colors.nuke("[SMART ACCURACY LAYER]"))
        print("=" * 70)
        summary = enhanced.get("accuracy_summary", {})
        counts = summary.get("confidence_counts", {})
        print(f"Unique findings:       {summary.get('unique_findings', len(enhanced.get('vulnerabilities', [])))}")
        print(f"Duplicates removed:    {summary.get('duplicates_removed', 0)}")
        print(f"High confidence:       {counts.get('HIGH', 0)}")
        print(f"Medium confidence:     {counts.get('MEDIUM', 0)}")
        print(f"Low confidence/noisy:  {counts.get('LOW', 0)}")

        noisy = summary.get("needs_manual_review", [])
        if noisy:
            print(ums.Colors.warning("\nFindings needing manual review:"))
            for item in noisy[:10]:
                warnings = "; ".join(item.get("warnings", [])[:2])
                print(f"  - {item.get('type')} at {item.get('location')} [{item.get('confidence')}] {warnings}")

        # Regenerate reports after smart post-processing so JSON contains accuracy metadata.
        try:
            enhanced["reports"] = self.reporter.generate_all_reports(enhanced)
        except Exception as exc:
            print(ums.Colors.warning(f"[!] Could not regenerate enhanced reports: {exc}"))

        print("=" * 70 + "\n")
        return enhanced


def build_config(args) -> ums.ScanConfig:
    config = ums.ScanConfig(
        target=args.target or "",
        full_scan=args.full,
        exploit=args.exploit,
        threads=args.threads,
        timeout=args.timeout,
        delay=args.delay,
        proxy=args.proxy,
        output_dir=args.output,
        verbose=args.verbose,
        stealth=args.stealth,
    )
    if args.stealth:
        config.delay = max(args.delay, 2.0)
        config.threads = min(args.threads, 2)
        print(ums.Colors.warning("[!] Stealth mode: delay=2s, threads=2"))
    if args.fast:
        config.delay = 0
        config.threads = min(args.threads, 20)
        print(ums.Colors.warning("[!] Fast mode: delay=0s, threads=20"))
    return config


def main():
    parser = argparse.ArgumentParser(
        description="Smart accuracy runner for ULTIMATE_MEGA_SCANNER",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 ULTIMATE_MEGA_SCANNER_SMART.py --target https://example.com
  python3 ULTIMATE_MEGA_SCANNER_SMART.py --target https://example.com --full
  python3 ULTIMATE_MEGA_SCANNER_SMART.py --target-list targets.txt --threads 5
        """,
    )
    parser.add_argument("--target", "-t", help="Target URL")
    parser.add_argument("--target-list", help="File with list of targets")
    parser.add_argument("--full", action="store_true", help="Full comprehensive scan")
    parser.add_argument("--fast", action="store_true", help="Fast scan")
    parser.add_argument("--stealth", action="store_true", help="Stealth mode")
    parser.add_argument("--exploit", action="store_true", help="Pass through original scanner exploit mode")
    parser.add_argument("--output", "-o", default="output/mega_scan_smart", help="Output directory")
    parser.add_argument("--threads", type=int, default=10, help="Number of threads")
    parser.add_argument("--timeout", type=int, default=30, help="Request timeout")
    parser.add_argument("--delay", type=float, default=0.1, help="Delay between requests")
    parser.add_argument("--proxy", help="Proxy URL")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    args = parser.parse_args()

    if not args.target and not args.target_list:
        parser.print_help()
        print(f"\n{ums.Colors.critical('[ERROR]')} Please specify --target or --target-list\n")
        sys.exit(1)

    config = build_config(args)

    try:
        if args.target:
            scanner = SmartUltimateMegaScanner(config)
            scanner.scan(args.target)
        else:
            with open(args.target_list, "r", encoding="utf-8") as f:
                targets = [line.strip() for line in f if line.strip() and not line.startswith("#")]
            if not targets:
                print(ums.Colors.critical("[ERROR] No valid targets found in file"))
                sys.exit(1)
            print(ums.Colors.nuke(f"\n[*] Scanning {len(targets)} targets with smart accuracy layer...\n"))
            for i, target in enumerate(targets, 1):
                print(ums.Colors.nuke(f"\n{'='*70}"))
                print(ums.Colors.nuke(f"TARGET {i}/{len(targets)}"))
                print(ums.Colors.nuke(f"{'='*70}\n"))
                scanner = SmartUltimateMegaScanner(config)
                scanner.scan(target)
                if i < len(targets):
                    time.sleep(5)
    except KeyboardInterrupt:
        print(ums.Colors.warning("\n\n[!] Scan interrupted by user"))
        sys.exit(0)
    except Exception as exc:
        print(ums.Colors.critical(f"\n[!] Fatal error: {exc}"))
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
