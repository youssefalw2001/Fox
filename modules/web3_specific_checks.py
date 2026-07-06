#!/usr/bin/env python3
"""
💀🔥 WEB3 SPECIFIC CHECKS - FOX'S SPECIALIZED EXPLOITS 🔥💀

Web3-specific vulnerability checks for Stage 3 active testing.
Integrates with ULTIMATE_MEGA_SCANNER for authorized exploitation.
"""

import requests
import json
import re
from typing import List, Dict
from dataclasses import dataclass

@dataclass
class Web3Vulnerability:
    """Web3-specific vulnerability finding"""
    type: str
    severity: str
    location: str
    description: str
    evidence: str
    remediation: str
    exploitable: bool
    web3_specific: bool = True

class Web3SpecificChecks:
    """Web3/Solana-specific vulnerability checks"""
    
    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Security Research)'
        })
    
    def check_solana_authority_exposure(self, target: str, program_ids: List[str]) -> List[Web3Vulnerability]:
        """Check for exposed Solana program authority information"""
        vulns = []
        
        # Check if program authority info is exposed in frontend
        try:
            r = self.session.get(target, timeout=self.timeout)
            
            for program_id in program_ids[:5]:  # Check first 5
                if program_id in r.text:
                    # Check for authority/upgrade authority exposure
                    if 'authority' in r.text.lower() or 'upgradeAuthority' in r.text:
                        vulns.append(Web3Vulnerability(
                            type="SOLANA_AUTHORITY_EXPOSURE",
                            severity="MEDIUM",
                            location=f"Program ID: {program_id}",
                            description="Solana program authority information exposed in frontend",
                            evidence=f"Program ID {program_id} found with authority references",
                            remediation="Avoid exposing program authority addresses in frontend code",
                            exploitable=False
                        ))
        except:
            pass
        
        return vulns
    
    def check_rpc_url_exposure(self, target: str, rpc_urls: List[str]) -> List[Web3Vulnerability]:
        """Check for private RPC URL exposure"""
        vulns = []
        
        for rpc_url in rpc_urls:
            # Check if it's a private/paid RPC (not public Solana RPC)
            if any(x in rpc_url.lower() for x in ['api.', 'private', 'premium', 'pro.', 'rpc.', 'node.']):
                if 'api-mainnet-beta.solana.com' not in rpc_url:  # Not public
                    vulns.append(Web3Vulnerability(
                        type="PRIVATE_RPC_URL_EXPOSED",
                        severity="MEDIUM",
                        location="JavaScript Bundle",
                        description="Private/paid RPC URL exposed in frontend code",
                        evidence=f"RPC URL: {rpc_url[:50]}...",
                        remediation="Use environment variables and server-side proxy for RPC calls",
                        exploitable=True
                    ))
        
        return vulns
    
    def check_privy_auth_misconfig(self, target: str) -> List[Web3Vulnerability]:
        """Check for Privy authentication misconfiguration"""
        vulns = []
        
        try:
            r = self.session.get(target, timeout=self.timeout)
            
            # Check for exposed Privy config
            if 'PRIVY_APP_ID' in r.text or 'privyAppId' in r.text:
                # Check if client ID is exposed (should be fine) vs secret (bad)
                if 'PRIVY_CLIENT_SECRET' in r.text or 'privyClientSecret' in r.text:
                    vulns.append(Web3Vulnerability(
                        type="PRIVY_SECRET_EXPOSED",
                        severity="CRITICAL",
                        location="Frontend Code",
                        description="Privy client secret exposed in frontend (should only be server-side)",
                        evidence="PRIVY_CLIENT_SECRET found in public JavaScript",
                        remediation="Move Privy secret to server-side environment variables",
                        exploitable=True
                    ))
        except:
            pass
        
        return vulns
    
    def check_socketio_timing_attack(self, target: str) -> List[Web3Vulnerability]:
        """Check for Socket.IO timing attack vectors (crash games)"""
        vulns = []
        
        try:
            # Check if Socket.IO is used
            r = self.session.get(target, timeout=self.timeout)
            
            if 'socket.io' in r.text.lower():
                # Check for crash game indicators
                crash_indicators = ['serverseedhash', 'clientseed', 'multiplier', 'crash']
                found_indicators = [ind for ind in crash_indicators if ind in r.text.lower()]
                
                if len(found_indicators) >= 2:
                    vulns.append(Web3Vulnerability(
                        type="SOCKETIO_CRASH_GAME_DETECTED",
                        severity="HIGH",
                        location="Socket.IO Implementation",
                        description="Crash game using Socket.IO - potential timing attack surface",
                        evidence=f"Found indicators: {', '.join(found_indicators)}",
                        remediation="Implement server-side timing validation, use secure random with sufficient delay",
                        exploitable=False  # Requires deep timing analysis
                    ))
        except:
            pass
        
        return vulns
    
    def check_wallet_drainer_vectors(self, target: str) -> List[Web3Vulnerability]:
        """Check for wallet drainer attack vectors"""
        vulns = []
        
        try:
            r = self.session.get(target, timeout=self.timeout)
            
            # Check for unsafe wallet connection patterns
            if 'wallet-adapter' in r.text.lower() or 'connectWallet' in r.text:
                # Check for XSS that could inject malicious wallet requests
                xss_vectors = ['<script>', 'onerror=', 'onload=', 'javascript:']
                
                # Test a simple XSS payload in common params
                test_params = ['?q=<script>alert(1)</script>', '?search=<img src=x onerror=alert(1)>']
                
                for param in test_params:
                    try:
                        r_test = self.session.get(target + param, timeout=5)
                        
                        if any(vec in r_test.text for vec in xss_vectors):
                            # Check if it's not encoded
                            if '<script>alert(1)</script>' in r_test.text or 'onerror=alert' in r_test.text:
                                vulns.append(Web3Vulnerability(
                                    type="XSS_WALLET_DRAINER_VECTOR",
                                    severity="CRITICAL",
                                    location=f"Parameter: {param.split('=')[0][1:]}",
                                    description="XSS vulnerability in wallet-enabled site - potential wallet drainer vector",
                                    evidence="Unencoded script tags reflected in response",
                                    remediation="Implement strict CSP, encode all user input, use wallet interaction confirmation",
                                    exploitable=True
                                ))
                                break
                    except:
                        continue
        except:
            pass
        
        return vulns
    
    def check_token_approval_risks(self, target: str, program_ids: List[str]) -> List[Web3Vulnerability]:
        """Check for unlimited token approval risks"""
        vulns = []
        
        try:
            r = self.session.get(target, timeout=self.timeout)
            
            # Check for token approval patterns
            approval_patterns = ['approve', 'setApprovalForAll', 'increaseAllowance']
            
            for pattern in approval_patterns:
                if pattern in r.text:
                    # Check if there's a max uint check (unlimited approval)
                    if 'MAX_UINT' in r.text or '0xffffffff' in r.text or 'MAX_U64' in r.text:
                        vulns.append(Web3Vulnerability(
                            type="UNLIMITED_TOKEN_APPROVAL",
                            severity="MEDIUM",
                            location="Token Approval Logic",
                            description="Site may request unlimited token approvals",
                            evidence=f"Found {pattern} with MAX_UINT pattern",
                            remediation="Request exact approval amounts, not unlimited",
                            exploitable=False
                        ))
                        break
        except:
            pass
        
        return vulns
    
    def run_all_web3_checks(self, target: str, site_data: Dict) -> List[Web3Vulnerability]:
        """Run all Web3-specific checks"""
        all_vulns = []
        
        # Extract data from passive stage
        program_ids = site_data.get('js_analysis', {}).get('program_ids', [])
        rpc_urls = site_data.get('js_analysis', {}).get('rpc_urls', [])
        
        print(f"  [→] Web3-specific checks for {target}")
        
        # Run checks
        all_vulns.extend(self.check_solana_authority_exposure(target, program_ids))
        all_vulns.extend(self.check_rpc_url_exposure(target, rpc_urls))
        all_vulns.extend(self.check_privy_auth_misconfig(target))
        all_vulns.extend(self.check_socketio_timing_attack(target))
        all_vulns.extend(self.check_wallet_drainer_vectors(target))
        all_vulns.extend(self.check_token_approval_risks(target, program_ids))
        
        if all_vulns:
            print(f"    [✓] Found {len(all_vulns)} Web3-specific findings")
        else:
            print(f"    [·] No Web3-specific vulnerabilities found")
        
        return all_vulns
