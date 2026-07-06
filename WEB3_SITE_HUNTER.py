#!/usr/bin/env python3
"""
💀🔥 WEB3 SITE HUNTER - STAGE 1: DISCOVERY 🔥💀

Discovers Web3/Solana/DeFi sites from public sources.
Outputs candidates.json for passive ranking.

Author: Fox
Partner: Jack
Status: STAGE 1 - DISCOVERY ENGINE

USAGE:
    python3 WEB3_SITE_HUNTER.py --limit 50 --out candidates.json
    python3 WEB3_SITE_HUNTER.py --category solana --limit 30
"""

import sys
import argparse
import json
from datetime import datetime
from pathlib import Path

# Add modules to path
sys.path.insert(0, str(Path(__file__).parent / 'modules'))

from collector import Web3SiteCollector

def print_banner():
    """Print Fox's banner"""
    banner = """
    ╔═══════════════════════════════════════════════════════════════╗
    ║                                                               ║
    ║   ██╗    ██╗███████╗██████╗ ██████╗     ██╗  ██╗██╗   ██╗███╗   ██╗████████╗███████╗██████╗   ║
    ║   ██║    ██║██╔════╝██╔══██╗╚════██╗    ██║  ██║██║   ██║████╗  ██║╚══██╔══╝██╔════╝██╔══██╗  ║
    ║   ██║ █╗ ██║█████╗  ██████╔╝ █████╔╝    ███████║██║   ██║██╔██╗ ██║   ██║   █████╗  ██████╔╝  ║
    ║   ██║███╗██║██╔══╝  ██╔══██╗ ╚═══██╗    ██╔══██║██║   ██║██║╚██╗██║   ██║   ██╔══╝  ██╔══██╗  ║
    ║   ╚███╔███╔╝███████╗██████╔╝██████╔╝    ██║  ██║╚██████╔╝██║ ╚████║   ██║   ███████╗██║  ██║  ║
    ║    ╚══╝╚══╝ ╚══════╝╚═════╝ ╚═════╝     ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═══╝   ╚═╝   ╚══════╝╚═╝  ╚═╝  ║
    ║                                                               ║
    ║              💀🔥 STAGE 1: WEB3 SITE DISCOVERY 🔥💀           ║
    ║                                                               ║
    ║   [✓] Solana Ecosystem    [✓] DeFi Protocols                ║
    ║   [✓] Crash Games         [✓] NFT Marketplaces              ║
    ║   [✓] Wallet Apps         [✓] Bridge Apps                   ║
    ║                                                               ║
    ║   Built by: Fox | Partner: Jack | Stage 1 of 3              ║
    ╚═══════════════════════════════════════════════════════════════╝
    """
    print(banner)

def main():
    """Main execution"""
    parser = argparse.ArgumentParser(
        description='WEB3 SITE HUNTER - Discover Web3/Solana/DeFi sites from public sources'
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=50,
        help='Maximum number of sites to collect (default: 50)'
    )
    parser.add_argument(
        '--out',
        type=str,
        default='candidates.json',
        help='Output file (default: candidates.json)'
    )
    parser.add_argument(
        '--category',
        type=str,
        choices=['all', 'solana', 'defi', 'crash-game', 'nft', 'wallet', 'bridge'],
        default='all',
        help='Filter by category (default: all)'
    )
    
    args = parser.parse_args()
    
    print_banner()
    
    print(f"""
═══════════════════════════════════════════════════════════════════
CONFIGURATION
═══════════════════════════════════════════════════════════════════
Limit:      {args.limit} sites
Category:   {args.category}
Output:     {args.out}
Started:    {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC
═══════════════════════════════════════════════════════════════════
""")
    
    # Initialize collector
    collector = Web3SiteCollector()
    
    # Collect sites
    try:
        sites = collector.collect_all(limit=args.limit)
        
        # Filter by category if specified
        if args.category != 'all':
            category_map = {
                'solana': 'solana-dapp',
                'defi': 'defi',
                'crash-game': 'crash-game',
                'nft': 'nft-marketplace',
                'wallet': 'wallet-app',
                'bridge': 'bridge-app'
            }
            target_category = category_map.get(args.category)
            if target_category:
                sites = [s for s in sites if s['category'] == target_category]
                print(f"\n  [→] Filtered to {len(sites)} {args.category} sites")
        
        # Save to file
        output_data = {
            "discovered_at": datetime.utcnow().isoformat() + "Z",
            "total_sites": len(sites),
            "category_filter": args.category,
            "sites": sites
        }
        
        with open(args.out, 'w') as f:
            json.dump(output_data, f, indent=2)
        
        print(f"""
═══════════════════════════════════════════════════════════════════
DISCOVERY COMPLETE
═══════════════════════════════════════════════════════════════════
Total sites:     {len(sites)}
Output file:     {args.out}
Next step:       python3 PASSIVE_RISK_RANKER.py --input {args.out}
═══════════════════════════════════════════════════════════════════

💀 Stage 1 complete. Ready for passive ranking.
""")
        
        # Print summary by category
        categories = {}
        for site in sites:
            cat = site['category']
            categories[cat] = categories.get(cat, 0) + 1
        
        print("\nBREAKDOWN BY CATEGORY:")
        for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
            print(f"  {cat:20s} {count:3d} sites")
        
        return 0
        
    except Exception as e:
        print(f"\n[!] ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())
