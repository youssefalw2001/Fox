#!/usr/bin/env python3
"""
Fox Phantom dApp Cataloger

Finds fresh Phantom/Solana-looking dApp websites from seed URLs or URL lists.
It does not exploit, attack, or auto-scan vulnerabilities. It catalogs and ranks
public dApp candidates by Phantom/Solana markers, freshness, and topic relevance.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from modules.phantom_dapp_catalog import (
    expand_from_seed_pages,
    rank_dapps,
    read_candidates,
    write_outputs,
)

DEFAULT_SEEDS = [
    "https://dappradar.com/rankings/protocol/solana",
    "https://www.alchemy.com/dapps/solana",
    "https://solana.com/ecosystem",
]


def main() -> None:
    parser = argparse.ArgumentParser(description="Find and rank fresh Phantom/Solana dApp sites")
    parser.add_argument("--input", "-i", help="Text file of candidate URLs, one per line")
    parser.add_argument("--seed", action="append", default=[], help="Seed page to extract public URLs from; can be repeated")
    parser.add_argument("--use-default-seeds", action="store_true", help="Use built-in public Solana ecosystem seed pages")
    parser.add_argument("--output", "-o", default="phantom_sites_new.txt", help="Output text file of ranked URLs")
    parser.add_argument("--json", default="phantom_sites_ranked.json", help="Output JSON file with scores/reasons")
    parser.add_argument("--seen", default="seen_phantom_sites.json", help="Persistent seen-history JSON")
    parser.add_argument("--limit", type=int, default=50, help="Max URLs to output")
    parser.add_argument("--min-score", type=int, default=30, help="Minimum score to include")
    parser.add_argument("--timeout", type=int, default=8, help="HTTP timeout per request")
    parser.add_argument("--include-seen", action="store_true", help="Include previously seen domains too")
    args = parser.parse_args()

    candidates = []
    if args.input:
        candidates.extend(read_candidates(args.input))

    seeds = list(args.seed)
    if args.use_default_seeds:
        seeds.extend(DEFAULT_SEEDS)

    if seeds:
        print(f"[*] Expanding candidates from {len(seeds)} seed page(s)...")
        candidates.extend(expand_from_seed_pages(seeds, timeout=args.timeout))

    if not candidates:
        print("[!] No candidates provided. Use --input urls.txt, --seed URL, or --use-default-seeds")
        return

    print(f"[*] Candidate URLs collected: {len(set(candidates))}")
    ranked = rank_dapps(
        candidates,
        seen_path=args.seen,
        timeout=args.timeout,
        min_score=args.min_score,
        fresh_only=not args.include_seen,
    )[: args.limit]

    write_outputs(ranked, args.output, args.json)

    print(f"[✓] Fresh Phantom/Solana dApps: {len(ranked)}")
    print(f"[✓] URL output: {args.output}")
    print(f"[✓] Ranked JSON: {args.json}")
    print(f"[✓] Seen history: {args.seen}")

    if ranked:
        print("\nTop results:")
        for item in ranked[:10]:
            print(f"  {item.score:3d}  {item.verdict:24s}  {item.url}")


if __name__ == "__main__":
    main()
