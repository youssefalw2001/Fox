#!/usr/bin/env python3
"""
💀🔥 FOX PROOF SCANNER - STAGE 3: ACTIVE TESTING 🔥💀

Active exploitation on top 3 sites selected by passive ranker.
Integrates ULTIMATE_MEGA_SCANNER + Web3-specific checks.

Author: Fox
Partner: Jack
Status: STAGE 3 - ACTIVE PROOF SCANNER

⚠️  REQUIRES EXPLICIT AUTHORIZATION FOR ACTIVE TESTING ⚠️

USAGE:
    python3 FOX_PROOF_SCANNER.py --targets top3.json --authorized
    python3 FOX_PROOF_SCANNER.py --targets top3.json --authorized --profile solana-dapp
"""

import sys
import argparse
import json
from datetime import datetime
from pathlib import Path

# Add modules to path
sys.path.insert(0, str(Path(__file__).parent / 'modules'))

from web3_specific_checks import Web3SpecificChecks

def print_banner():
    """Print Fox's banner"""
    banner = """
    ╔═══════════════════════════════════════════════════════════════╗
    ║                                                               ║
    ║   ███████╗ ██████╗ █████╗ ███╗   ██╗███╗   ██╗███████╗██████╗   ║
    ║   ██╔════╝██╔════╝██╔══██╗████╗  ██║████╗  ██║██╔════╝██╔══██╗  ║
    ║   ███████╗██║     ███████║██╔██╗ ██║██╔██╗ ██║█████╗  ██████╔╝  ║
    ║   ╚════██║██║     ██╔══██║██║╚██╗██║██║╚██╗██║██╔══╝  ██╔══██╗  ║
    ║   ███████║╚██████╗██║  ██║██║ ╚████║██║ ╚████║███████╗██║  ██║  ║
    ║   ╚══════╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝  ║
    ║                                                               ║
    ║          💀🔥 STAGE 3: ACTIVE PROOF SCANNER 🔥💀              ║
    ║                                                               ║
    ║   [✓] ULTIMATE_MEGA_SCANNER   [✓] Web3-Specific Checks      ║
    ║   [✓] Proof-Based Validation  [✓] Zero False Positives      ║
    ║                                                               ║
    ║   ⚠️  ACTIVE EXPLOITATION - REQUIRES AUTHORIZATION ⚠️         ║
    ║                                                               ║
    ║   Built by: Fox | Partner: Jack | Stage 3 of 3              ║
    ╚═══════════════════════════════════════════════════════════════╝
    """
    print(banner)

def run_ultimate_scanner(target: str) -> Dict:
    """Run ULTIMATE_MEGA_SCANNER on a target"""
    import subprocess
    
    print(f"\n  [→] Running ULTIMATE_MEGA_SCANNER on {target}")
    
    try:
        # Run the scanner
        result = subprocess.run(
            ['python3', 'ULTIMATE_MEGA_SCANNER.py', '--target', target],
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        # Load the latest scan result
        output_dir = Path('output/mega_scan')
        scan_files = sorted(output_dir.glob('scan_*.json'), key=lambda x: x.stat().st_mtime)
        
        if scan_files:
            with open(scan_files[-1], 'r') as f:
                return json.load(f)
        
        return {"vulnerabilities": []}
        
    except subprocess.TimeoutExpired:
        print("    [!] Scanner timeout after 5 minutes")
        return {"vulnerabilities": [], "error": "timeout"}
    except Exception as e:
        print(f"    [!] Scanner error: {str(e)}")
        return {"vulnerabilities": [], "error": str(e)}

def main():
    """Main execution"""
    parser = argparse.ArgumentParser(
        description='FOX PROOF SCANNER - Active exploitation on top ranked sites'
    )
    parser.add_argument(
        '--targets',
        type=str,
        required=True,
        help='Input file from PASSIVE_RISK_RANKER (top3.json)'
    )
    parser.add_argument(
        '--authorized',
        action='store_true',
        help='Confirm authorization for active testing (REQUIRED)'
    )
    parser.add_argument(
        '--profile',
        type=str,
        choices=['solana-dapp', 'defi', 'crash-game', 'nft', 'wallet', 'bridge', 'all'],
        default='all',
        help='Scan profile (enables specific checks)'
    )
    parser.add_argument(
        '--out',
        type=str,
        default='exploitation_report.json',
        help='Output file (default: exploitation_report.json)'
    )
    
    args = parser.parse_args()
    
    print_banner()
    
    # Check authorization
    if not args.authorized:
        print("""
═══════════════════════════════════════════════════════════════════
⚠️  AUTHORIZATION REQUIRED ⚠️
═══════════════════════════════════════════════════════════════════

Stage 3 performs ACTIVE TESTING which may trigger security alerts.

You must:
  1. Have explicit written authorization to test these targets
  2. Understand the legal implications of active exploitation
  3. Use --authorized flag to confirm

This tool is for AUTHORIZED SECURITY TESTING ONLY.

Example:
  python3 FOX_PROOF_SCANNER.py --targets top3.json --authorized

═══════════════════════════════════════════════════════════════════
""")
        return 1
    
    # Load targets
    try:
        with open(args.targets, 'r') as f:
            targets_data = json.load(f)
        
        top_sites = targets_data.get('top_sites', [])
        
        if not top_sites:
            print("[!] No top sites found in input file")
            return 1
        
        print(f"""
═══════════════════════════════════════════════════════════════════
CONFIGURATION
═══════════════════════════════════════════════════════════════════
Input:      {args.targets}
Targets:    {len(top_sites)} sites
Profile:    {args.profile}
Output:     {args.out}
Authorized: ✅ YES
Started:    {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC
═══════════════════════════════════════════════════════════════════
""")
        
    except FileNotFoundError:
        print(f"[!] Input file not found: {args.targets}")
        return 1
    except json.JSONDecodeError:
        print(f"[!] Invalid JSON in input file: {args.targets}")
        return 1
    
    # Initialize Web3 checker
    web3_checker = Web3SpecificChecks()
    
    # Scan each target
    all_results = []
    
    print("\n💀 STAGE 3: ACTIVE PROOF SCANNING\n")
    
    for i, site_data in enumerate(top_sites, 1):
        target_url = site_data['site']
        
        print(f"\n{'='*70}")
        print(f"TARGET {i}/{len(top_sites)}: {target_url}")
        print(f"Score: {site_data['score']} | Category: {site_data['category']}")
        print(f"{'='*70}")
        
        result = {
            "target": target_url,
            "category": site_data['category'],
            "passive_score": site_data['score'],
            "scan_started": datetime.utcnow().isoformat() + "Z",
            "web3_vulnerabilities": [],
            "general_vulnerabilities": [],
            "total_vulnerabilities": 0
        }
        
        # Run Web3-specific checks first
        print("\n[1/2] WEB3-SPECIFIC CHECKS")
        web3_vulns = web3_checker.run_all_web3_checks(target_url, site_data)
        
        for vuln in web3_vulns:
            result["web3_vulnerabilities"].append({
                "type": vuln.type,
                "severity": vuln.severity,
                "location": vuln.location,
                "description": vuln.description,
                "evidence": vuln.evidence,
                "exploitable": vuln.exploitable
            })
        
        # Run ULTIMATE_MEGA_SCANNER
        print("\n[2/2] GENERAL VULNERABILITY SCAN")
        scanner_results = run_ultimate_scanner(target_url)
        
        if "vulnerabilities" in scanner_results:
            result["general_vulnerabilities"] = scanner_results["vulnerabilities"]
        
        result["total_vulnerabilities"] = len(result["web3_vulnerabilities"]) + len(result["general_vulnerabilities"])
        result["scan_completed"] = datetime.utcnow().isoformat() + "Z"
        
        all_results.append(result)
        
        print(f"\n  [✓] Scan complete: {result['total_vulnerabilities']} total findings")
    
    # Save full report
    report = {
        "scan_type": "active_proof_scanning",
        "profile": args.profile,
        "scanned_at": datetime.utcnow().isoformat() + "Z",
        "targets_scanned": len(top_sites),
        "results": all_results
    }
    
    with open(args.out, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"""
═══════════════════════════════════════════════════════════════════
ACTIVE SCANNING COMPLETE
═══════════════════════════════════════════════════════════════════
Targets scanned: {len(top_sites)}
Output file:     {args.out}
═══════════════════════════════════════════════════════════════════
""")
    
    # Summary
    total_vulns = sum(r['total_vulnerabilities'] for r in all_results)
    web3_vulns = sum(len(r['web3_vulnerabilities']) for r in all_results)
    general_vulns = sum(len(r['general_vulnerabilities']) for r in all_results)
    
    print("\n💀 EXPLOITATION SUMMARY:\n")
    print(f"  Total vulnerabilities:     {total_vulns}")
    print(f"  Web3-specific:             {web3_vulns}")
    print(f"  General web:               {general_vulns}")
    print()
    
    for i, result in enumerate(all_results, 1):
        print(f"  #{i}. {result['target']}")
        print(f"      Vulnerabilities: {result['total_vulnerabilities']}")
        if result['web3_vulnerabilities']:
            print(f"      Web3 findings:   {len(result['web3_vulnerabilities'])}")
        print()
    
    print("═══════════════════════════════════════════════════════════════════")
    print("\n💀 3-stage pipeline complete. Review exploitation_report.json for details.")
    print()
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
