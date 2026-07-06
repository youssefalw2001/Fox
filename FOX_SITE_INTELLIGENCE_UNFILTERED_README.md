# FOX SITE INTELLIGENCE - UNFILTERED MODE

## ⚠️ WARNING: AUTHORIZED USE ONLY

The `--unfiltered` flag disables all output redaction and is **only for authorized security review** (e.g., bug bounty judges, internal security audits, authorized pentests).

---

## What Changes with `--unfiltered`?

### **WITHOUT --unfiltered (Default - Safe Mode):**
```bash
python3 FOX_SITE_INTELLIGENCE.py --target https://target.com --data-intel --judge-mode
```

**Output:**
- ✅ Secrets are REDACTED: `sk_liv...<STRIPE_SECRET_KEY:redacted>...9GhI`
- ✅ Passwords are MASKED: `DATABASE_URL=<redacted>`
- ✅ JWT tokens are TRUNCATED: `eyJhbGci...<redacted-jwt>`
- ✅ Evidence previews are LIMITED to 600 chars
- ✅ Only SHA-256 hashes of full responses

---

### **WITH --unfiltered (Judge Review Mode):**
```bash
python3 FOX_SITE_INTELLIGENCE.py --target https://target.com --data-intel --judge-mode --unfiltered
```

**Output:**
- ✅ Secrets are FULL: `stripe_sk_live_[FULL_KEY_HERE]`
- **Passwords are VISIBLE:** `postgres://admin:XXXXXXXX@db.example.com:5432/production`
- ⚠️ JWT tokens are COMPLETE: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0...`
- ⚠️ Full HTTP response bodies stored (not just previews)
- ⚠️ Complete unredacted evidence in JSON reports

---

## Comparison Example

### Test File (test_secrets_demo.html):
```javascript
const config = {
    AWS_ACCESS_KEY_ID: 'AWS_KEY_[EXAMPLE]',
    STRIPE_SECRET_KEY: 'STRIPE_KEY_[EXAMPLE]',
    JWT_SECRET: 'JWT_SECRET_[EXAMPLE]',
    DATABASE_URL: 'postgres://admin:PASSWORD@db.example.com:5432/dbname'
};
```

### **Redacted Output (Default):**
```json
{
  "type": "STRIPE_SECRET_KEY",
  "evidence": "sk_liv...<STRIPE_SECRET_KEY:redacted>...9GhI",
  "severity": "HIGH",
  "confidence": 94
}
```

### **Unfiltered Output (--unfiltered):**
```json
{
  "type": "STRIPE_SECRET_KEY",
  "evidence": "stripe_sk_live_[FULL_KEY_VISIBLE_HERE]",
  "severity": "HIGH",
  "confidence": 94
}
```

---

## Usage

### Basic Intelligence Scan (Safe):
```bash
python3 FOX_SITE_INTELLIGENCE.py \
    --target https://target.com \
    --deep \
    --data-intel \
    --gear3 \
    --lab-mode \
    --judge-mode
```

### Full Unredacted Review (Authorized Only):
```bash
python3 FOX_SITE_INTELLIGENCE.py \
    --target https://target.com \
    --deep \
    --data-intel \
    --gear3 \
    --lab-mode \
    --judge-mode \
    --unfiltered
```

---

## Output Files

### With `--unfiltered`:
- `output/fox_site_intelligence/fox_report.json` - Full unredacted findings
- `output/fox_site_intelligence/data_exposure.json` - Complete secrets (NOT redacted)
- `output/fox_site_intelligence/judge_review_report.json` - Full evidence bodies

### Without `--unfiltered`:
- Same files, but secrets are redacted with `<CREDENTIAL_TYPE:redacted>` format

---

## Security Notes

1. **Never commit `--unfiltered` output to version control**
2. **Never share `--unfiltered` reports publicly**
3. **Use only in authorized security assessments**
4. **Rotate any secrets found immediately after review**
5. **Store unfiltered reports encrypted at rest**

---

## Affected Modules

The `--unfiltered` flag modifies behavior in:

1. **`modules/data_exposure_intel.py`**
   - `redact_secret(text, unfiltered=True)` → Returns full text
   - `build_data_exposure_report(blobs, unfiltered=True)` → No masking

2. **`modules/judge_review_mode.py`**
   - `evidence_record(value, full_evidence=True)` → Stores complete responses
   - `build_judge_review_report(result, full_evidence=True)` → No truncation

3. **`FOX_SITE_INTELLIGENCE.py`**
   - Passes `unfiltered=args.unfiltered` to all intel modules
   - Displays warning banner when active

---

## Legal & Ethical Use

This tool is for **authorized security testing only**. Unauthorized use may violate:
- Computer Fraud and Abuse Act (CFAA)
- Wiretap Act
- Data protection regulations (GDPR, CCPA)
- Bug bounty program rules
- Terms of Service

**Always obtain explicit written authorization before scanning any target.**

---

## Testing

Test the difference with the included demo file:

```bash
# Generate demo file with fake secrets
python3 -c "
from modules.data_exposure_intel import scan_text_for_exposures

text = '''
const config = {
    STRIPE_SECRET_KEY: 'stripe_key_[EXAMPLE]',
    DATABASE_URL: 'postgres://admin:XXXXXXXX@db.example.com:5432/production'
};
'''

print('REDACTED:')
findings = scan_text_for_exposures('test', text, unfiltered=False)
for f in findings:
    print(f'  {f.type}: {f.evidence}')

print('\\nUNFILTERED:')
findings = scan_text_for_exposures('test', text, unfiltered=True)
for f in findings:
    print(f'  {f.type}: {f.evidence}')
"
```

Expected output:
```
REDACTED:
  STRIPE_SECRET_KEY: stripe_...<STRIPE_SECRET_KEY:redacted>...XXXX
  DATABASE_URL: postgr...<DATABASE_URL:redacted>...tion

UNFILTERED:
  STRIPE_SECRET_KEY: stripe_sk_live_[FULL_KEY_HERE]
  DATABASE_URL: postgres://admin:XXXXXXXX@db.example.com:5432/production
```

---

## Questions?

Read the source:
- `FOX_SITE_INTELLIGENCE.py` - Main scanner with `--unfiltered` flag
- `modules/data_exposure_intel.py` - Secret detection and redaction logic
- `modules/judge_review_mode.py` - Evidence storage logic

---

**🦊 Built by Fox for authorized security research.**
