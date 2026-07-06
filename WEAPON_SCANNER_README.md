# 🦊💀 FOX WEAPON SCANNER 💀🦊

**Proof-based penetration testing scanner with aggressive exploitation**

## Features

### ✅ ZERO FALSE POSITIVES
- **Strict format validation** for all credentials
  - Stripe: validates exact 24-char format after prefix
  - AWS: validates AKIA + 16 UPPERCASE chars only
  - Google: validates AIza + 35 chars
  - JWT: validates 3-part structure + decodable header
- **HTML rejection** - filters out Vercel/SPA fallback pages
- **Placeholder detection** - rejects test/example/placeholder values
- **2-phase validation** - pattern match → format validate → report

### 💀 AGGRESSIVE EXPLOITATION
- **.git reconstruction** - downloads exposed .git files for source code recovery
- **Backup extraction** - finds and downloads exposed backup files (.zip, .sql, .tar.gz)
- **SSRF cloud metadata** - exploits SSRF to extract AWS/Azure/GCP credentials
- **SQLi auto-dump** - detects SQL injection and provides sqlmap command for data extraction
- **JavaScript deep analysis** - scans all JS bundles for hardcoded secrets
- **Config file enumeration** - hunts .env, config.json, credentials files

## Usage

### Basic Scan (Aggressive Mode)
```bash
python3 FOX_WEAPON_SCANNER.py https://target.com
```

### Passive Reconnaissance Mode
```bash
python3 FOX_WEAPON_SCANNER.py https://target.com --passive
```

## Scan Phases

### Phase 1: Reconnaissance
- Technology fingerprinting (Next.js, React, server detection)
- Framework identification

### Phase 2: Secret Hunting (STRICT validation)
- **Config files**: .env, .aws/credentials, config.json, appsettings.json
- **JavaScript secrets**: Deep analysis of all JS bundles
- **Memory patterns**: API endpoints leaking credentials

### Phase 3: Aggressive Exploitation (if enabled)
- **Git exposure**: Download .git/HEAD, .git/config, .git/index, .git/logs
- **Backup files**: Extract backup.zip, db.sql, dump.sql, site.tar.gz
- **SSRF clouds**: Target AWS/Azure/GCP metadata endpoints for credential extraction
- **SQLi dump**: Detect SQL injection and generate exploitation commands

### Phase 4: Reporting
- Grouped by severity (CRITICAL/HIGH/MEDIUM/LOW)
- Detailed findings with proof
- JSON report export
- Exploitation commands included

## Output

### Console Output
```
🦊💀 FOX WEAPON SCANNER 💀🦊
Target: https://target.com
Mode: AGGRESSIVE
================================================================================

[Phase 1] Reconnaissance...
  [+] Detected: Frontend: Next.js

[Phase 2] Secret Hunting (STRICT validation)...
  [→] Hunting config files...
    [💀] /.env: 3 validated secrets
  [→] Hunting JavaScript secrets...
    [💀] /static/js/main.js: 2 validated secrets
  [→] Hunting memory patterns...

[Phase 3] AGGRESSIVE Exploitation...
  [→] Exploiting .git exposure...
    [🔥] .git/HEAD exposed!
    [💀] Downloaded: /.git/HEAD
    [💀] Downloaded: /.git/config
  [→] Exploiting backup files...
    [💀] /backup.zip: 52,428,800 bytes
  [→] Exploiting SSRF for cloud metadata...
    [💀] SSRF: /api/fetch?url= → AWS EC2 Metadata
  [→] Exploiting SQL injection...
    [💀] SQLi: /api/user?id=

[Phase 4] Generating Report...

================================================================================
SCAN COMPLETE: 6 findings
================================================================================

💀 CRITICAL: 6
🔥 HIGH: 0
⚠️  MEDIUM: 0
ℹ️  LOW: 0

================================================================================
DETAILED FINDINGS
================================================================================

💀 [CRITICAL] Exposed config file: /.env
   Category: Config Exposure
   Location: https://target.com/.env
   Description: Configuration file exposed with 3 validated secrets
   Proof:
      DATABASE_URL=SECRET (38 chars)
      STRIPE_SECRET_KEY=STRIPE_KEY (sk_live_xxxx...)
      AWS_ACCESS_KEY_ID=AWS_ACCESS_KEY (AKIAxxxxxxxx...)
   Remediation: Block access to config files, rotate all exposed credentials

💀 [CRITICAL] Secrets hardcoded in JavaScript
   Category: Secret Exposure
   Location: JavaScript bundles
   Description: Found 2 validated secrets in 1 JS files
   Proof:
      /static/js/main.js: STRIPE_KEY = sk_live_xxxx123...
      /static/js/main.js: AWS_KEY = AKIAxxxxxxEXAMPLE
   Remediation: Remove hardcoded secrets from client code, rotate all exposed credentials

💀 [CRITICAL] .git directory exposed
   Category: Information Disclosure
   Location: https://target.com/.git/
   Description: Full .git repository accessible, allowing source code reconstruction
   Proof:
      Downloaded 4 files:
      /.git/config (98 bytes)
      /.git/HEAD (23 bytes)
      /.git/index (1245 bytes)
      /.git/logs/HEAD (542 bytes)
   Exploitation: Use: git-dumper or GitHack to reconstruct full source
   Remediation: Block access to .git directory via web server config

📄 Report saved: fox_weapon_report_1234567890.json
```

### JSON Report
```json
{
  "target": "https://target.com",
  "scan_time": "2026-07-05T...",
  "total_findings": 6,
  "by_severity": {
    "CRITICAL": 6,
    "HIGH": 0,
    "MEDIUM": 0,
    "LOW": 0
  },
  "findings": [
    {
      "severity": "CRITICAL",
      "category": "Config Exposure",
      "title": "Exposed config file: /.env",
      "location": "https://target.com/.env",
      "description": "Configuration file exposed with 3 validated secrets",
      "proof": "DATABASE_URL=SECRET (38 chars)...",
      "exploitation": null,
      "remediation": "Block access to config files, rotate all exposed credentials",
      "timestamp": "2026-07-05T..."
    }
  ]
}
```

## Validation Logic

### Stripe Keys
```python
# Valid: sk_live_ or pk_live_ or sk_test_ + EXACTLY 24 alphanumeric chars
sk_live_[24_ALPHANUMERIC_CHARS]  ✅ (valid format - 24 chars after prefix)
sk_live_abcd1234                 ❌ (too short)
sk_live_your_key_here            ❌ (placeholder)
```

### AWS Access Keys
```python
# Valid: AKIA + EXACTLY 16 UPPERCASE alphanumeric chars
AKIA + 16_UPPERCASE_CHARS  ✅ (example format)
AKIAxxxxxxexample          ❌ (lowercase)
AKIA1234                   ❌ (too short)
```

### Google API Keys
```python
# Valid: AIza + EXACTLY 35 chars
AIza + 35_random_chars  ✅ (example format)
AIzaxxxxK                ❌ (too short)
```

### JWT Tokens
```python
# Valid: 3 parts (header.payload.signature), decodable header with "alg" field
eyJhbG...JWT_FORMAT...signature  ✅ (3 parts, valid header)
eyJhbGciOi.invalid               ❌ (invalid format)
```

## Comparison

| Feature | ULTIMATE_MEGA_SCANNER | FOX_WEAPON_SCANNER |
|---------|----------------------|--------------------|
| **Validation** | ✅ Strict format | ✅ Strict format |
| **False Positives** | ❌ Zero (merged validation) | ❌ Zero |
| **.git Exploitation** | ✅ Full dump + reconstruction | ✅ Key files download |
| **Backup Extraction** | ✅ Download + size reporting | ✅ Download + size reporting |
| **SSRF Exploitation** | ✅ Cloud metadata + credentials | ✅ Cloud metadata validation |
| **SQLi Exploitation** | ✅ Auto-dump with sqlmap | ✅ Error-based detection + sqlmap |
| **JS Analysis** | ✅ Deep 20+ files | ✅ Deep 15 files |
| **Config Hunting** | ✅ 13 paths | ✅ 10 paths |
| **Speed** | Aggressive (200+ checks) | Balanced (focused exploitation) |
| **Use Case** | Full pentest - everything | Proof-first bug bounty reports |

## When to Use Which Scanner

### Use FOX_WEAPON_SCANNER when:
- ✅ You want **clean proof-based reports** for bug bounties
- ✅ You need **zero false positives** (strict validation only)
- ✅ You want **aggressive exploitation** with clear proof
- ✅ You need **JSON export** for reporting
- ✅ You want **fast focused scans** (reconnaissance + exploitation)

### Use ULTIMATE_MEGA_SCANNER when:
- ✅ You need **comprehensive coverage** (200+ attack vectors)
- ✅ You want **XXE, IDOR, Open Redirect, JWT attacks** (not in FOX_WEAPON)
- ✅ You need **subdomain takeover** checks
- ✅ You want **brute-force testing** with multiple payloads
- ✅ You're doing **full penetration testing** (not just recon)

## Legal Notice

**AUTHORIZED SECURITY TESTING ONLY**

This tool is for authorized security testing on systems you own or have explicit written permission to test.

Unauthorized access to computer systems is illegal under:
- Computer Fraud and Abuse Act (CFAA) - United States
- Computer Misuse Act - United Kingdom  
- Similar laws in other jurisdictions

The authors are not responsible for misuse of this tool.

## Installation

```bash
pip3 install requests
python3 FOX_WEAPON_SCANNER.py --help
```

No additional dependencies required.

## License

Private - Authorized Use Only
