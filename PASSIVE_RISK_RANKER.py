#!/usr/bin/env python3
"""
💀🔥 PASSIVE RISK RANKER - STAGE 2: SCORING 🔥💀

Scores Web3 sites by public attack surface indicators.
Selects top 3 for authorized active testing.

Author: Fox
Partner: Jack
Status: STAGE 2 - PASSIVE RANKING ENGINE

USAGE:
    python3 PASSIVE_RISK_RANKER.py --input candidates.json --top 3 --out top3.json
    python3 PASSIVE_RISK_RANKER.py --input candidates.json
"""

import sys
import argparse
import json
from datetime import datetime
from pathlib import Path
from tqdm import tqdm

# Add modules to path
sys.path.insert(0, str(Path(__file__).parent / 'modules'))

from fingerprinter import StackFingerprinter
from js_analyzer import JSAnalyzer
from ranker import RiskRanker

def print_banner():
    """Print Fox's banner"""
    banner = """
    ╔═══════════════════════════════════════════════════════════════╗
    ║                                                               ║
    ║   ██████╗  █████╗ ███╗   ██╗██╗  ██╗███████╗██████╗        ║
    ║   ██╔══██╗██╔══██╗████╗  ██║██║ ██╔╝██╔════╝██╔══██╗       ║
    ║   ██████╔╝███████║██╔██╗ ██║█████╔╝ █████╗  ██████╔╝       ║
    ║   ██╔══██╗██╔══██║██║╚██╗██║██╔═██╗ ██╔══╝  ██╔══██╗       ║
    ║   ██║  ██║██║  ██║██║ ╚████║██║  ██╗███████╗██║  ██║       ║
    ║   ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝       ║
    ║                                                               ║
    ║            💀🔥 STAGE 2: PASSIVE RISK RANKING 🔥💀            ║
    ║                                                               ║
    ║   [✓] Stack Fingerprinting    [✓] JS Analysis               ║
    ║   [✓] Attack Surface Scoring  [✓] Top N Selection           ║
    ║                                                               ║
    ║   NO ACTIVE EXPLOITATION - PASSIVE INTELLIGENCE ONLY         ║
    ║                                                               ║
    ║   Built by: Fox | Partner: Jack | Stage 2 of 3              ║
    ╚═══════════════════════════════════════════════════════════════╝
    """
    print(banner)

def main():
    """Main execution"""
    parser = argparse.ArgumentParser(
        description='PASSIVE RISK RANKER - Score Web3 sites by public attack surface'
    )
    parser.add_argument(
        '--input',
        type=str,
        required=True,
        help='Input file from WEB3_SITE_HUNTER (candidates.json)'
    )
    parser.add_argument(
        '--top',
        type=int,
        default=3,
        help='Number of top sites to select (default: 3)'
    )
    parser.add_argument(
        '--out',
        type=str,
        default='top3.json',
        help='Output file (default: top3.json)'
    )
    
    args = parser.parse_args()
    
    print_banner()
    
    # Load input
    try:
        with open(args.input, 'r') as f:
            input_data = json.load(f)
        
        sites = input_data.get('sites', [])
        
        if not sites:
            print("[!] No sites found in input file")
            return 1
        
        print(f"""
═══════════════════════════════════════════════════════════════════
CONFIGURATION
═══════════════════════════════════════════════════════════════════
Input:      {args.input}
Sites:      {len(sites)} total
Top N:      {args.top}
Output:     {args.out}
Started:    {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC
═══════════════════════════════════════════════════════════════════
""")
        
    except FileNotFoundError:
        print(f"[!] Input file not found: {args.input}")
        return 1
    except json.JSONDecodeError:
        print(f"[!] Invalid JSON in input file: {args.input}")
        return 1
    
    # Initialize tools
    fingerprinter = StackFingerprinter()
    js_analyzer = JSAnalyzer()
    ranker = RiskRanker()
    
    print("\n💀 STAGE 2A: FINGERPRINTING TECH STACKS\n")
    
    scored_sites = []
    
    # Process each site
    for site_data in tqdm(sites, desc="Fingerprinting", unit="site"):
        site_url = site_data["site"]
        
        # Fingerprint stack
        fingerprint = fingerprinter.fingerprint_site(site_url)
        
        if not fingerprint.get("reachable"):
            continue
        
        # Analyze JS files
        js_files = fingerprint.get("js_files", [])
        js_analysis = js_analyzer.analyze_js_files(site_url, js_files)
        
        # Calculate score
        score_data = ranker.calculate_score(fingerprint, js_analysis)
        
        # Combine all data
        scored_site = {
            "site": site_url,
            "category": site_data.get("category", "unknown"),
            "source": site_data.get("source", "unknown"),
            "score": score_data["score"],
            "classification": score_data["classification"],
            "detected_features": score_data["detected_features"],
            "score_breakdown": score_data["score_breakdown"],
            "technologies": fingerprint.get("technologies", []),
            "frameworks": fingerprint.get("frameworks", []),
            "web3_indicators": fingerprint.get("web3_indicators", []),
            "js_analysis": {
                "files_analyzed": js_analysis.get("analyzed_files", 0),
                "api_urls": js_analysis.get("api_urls", []),
                "rpc_urls": js_analysis.get("rpc_urls", []),
                "websocket_urls": js_analysis.get("websocket_urls", []),
                "program_ids": js_analysis.get("program_ids", [])[:5],  # Top 5
                "admin_routes": js_analysis.get("admin_routes", [])
            }
        }
        
        scored_sites.append(scored_site)
    
    print(f"\n  [✓] Successfully fingerprinted {len(scored_sites)} sites")
    
    # Rank sites
    print("\n💀 STAGE 2B: RANKING BY ATTACK SURFACE\n")
    ranked_sites = ranker.rank_sites(scored_sites)
    top_sites = ranker.get_top_n(ranked_sites, args.top)
    
    # Save results
    output_data = {
        "ranked_at": datetime.utcnow().isoformat() + "Z",
        "total_sites_analyzed": len(scored_sites),
        "top_n": args.top,
        "top_sites": top_sites,
        "all_ranked_sites": ranked_sites
    }
    
    with open(args.out, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    print(f"""
═══════════════════════════════════════════════════════════════════
RANKING COMPLETE
═══════════════════════════════════════════════════════════════════
Sites analyzed:  {len(scored_sites)}
Output file:     {args.out}
Next step:       python3 FOX_PROOF_SCANNER.py --targets {args.out} --authorized
═══════════════════════════════════════════════════════════════════
""")
    
    # Display top sites
    print("\n💀 TOP {} SITES FOR AUTHORIZED FOLLOWUP:\n".format(args.top))
    
    for i, site in enumerate(top_sites, 1):
        print(f"#{i}. {site['site']}")
        print(f"    Score:          {site['score']}")
        print(f"    Category:       {site['category']}")
        print(f"    Classification: {site['classification']}")
        print(f"    Detected:       {', '.join(site['detected_features'][:5])}")
        if site['js_analysis']['program_ids']:
            print(f"    Program IDs:    {len(site['js_analysis']['program_ids'])} found")
        if site['js_analysis']['api_urls']:
            print(f"    API URLs:       {len(site['js_analysis']['api_urls'])} found")
        print()
    
    print("═══════════════════════════════════════════════════════════════════")
    print("\n💀 Stage 2 complete. Top sites selected for active testing.")
    print("   ⚠️  Active testing requires explicit authorization.")
    print()
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
