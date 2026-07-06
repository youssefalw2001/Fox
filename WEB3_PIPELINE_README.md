# 💀🔥 FOX'S 3-STAGE WEB3 INTELLIGENCE PIPELINE 🔥💀

**The cleanest Web3 target intelligence system ever built.**

Built by Fox | Partner: Jack | No false positives, no bullshit

---

## 🎯 **THE ARCHITECTURE**

```
STAGE 1: WEB3_SITE_HUNTER
    ↓
STAGE 2: PASSIVE_RISK_RANKER
    ↓
STAGE 3: FOX_PROOF_SCANNER (requires authorization)
```

### **What It Does:**

1. **Discovers 50+ Web3/Solana/DeFi sites** from public sources
2. **Scores them 0-100** by attack surface (passive intelligence only)
3. **Selects top 3** for authorized active testing
4. **Exploits with proof** (ULTIMATE_MEGA_SCANNER + Web3-specific checks)

---

## 🚀 **QUICK START**

### **Full Pipeline (One Command):**

```bash
# Passive intelligence only (Stages 1-2)
bash RUN_FULL_PIPELINE.sh --skip-stage-3

# Full pipeline with active testing (requires authorization)
bash RUN_FULL_PIPELINE.sh --authorized

# Custom configuration
bash RUN_FULL_PIPELINE.sh --limit 30 --top 5 --category solana --authorized
```

### **Individual Stages:**

```bash
# Stage 1: Discovery
python3 WEB3_SITE_HUNTER.py --limit 50 --out candidates.json

# Stage 2: Passive Ranking
python3 PASSIVE_RISK_RANKER.py --input candidates.json --top 3 --out top3.json

# Stage 3: Active Testing (requires authorization)
python3 FOX_PROOF_SCANNER.py --targets top3.json --authorized
```

---

## 📊 **STAGE 1: WEB3_SITE_HUNTER**

**What it does:** Discovers Web3/Solana/DeFi sites from public sources

**Sources:**
- Solana ecosystem (Raydium, Jupiter, Marinade, etc.)
- DeFi protocols (Uniswap, Curve, Aave, etc.)
- Crash/casino games (Stake, Rollbit, rugs.fun, etc.)
- NFT marketplaces (OpenSea, Magic Eden, Tensor, etc.)
- Wallet apps (Phantom, MetaMask, Solflare, etc.)
- Bridge apps (Wormhole, Allbridge, Portal, etc.)

**Output:** `candidates.json`

```json
{
  "total_sites": 50,
  "sites": [
    {
      "site": "https://jup.ag",
      "source": "solana_ecosystem_known",
      "category": "solana-dapp",
      "discovered_at": "2026-07-06T01:45:00Z"
    }
  ]
}
```

**Options:**
- `--limit N` - Max sites to collect (default: 50)
- `--category TYPE` - Filter: all, solana, defi, crash-game, nft, wallet, bridge
- `--out FILE` - Output file (default: candidates.json)

---

## 🎯 **STAGE 2: PASSIVE_RISK_RANKER**

**What it does:** Scores sites 0-100 by public attack surface, selects top 3

**Scoring System:**

| Indicator | Points | What It Means |
|-----------|--------|---------------|
| Solana wallet adapter | +25 | Wallet interaction enabled |
| Privy detected | +20 | Auth provider (potential misconfig) |
| Next.js/Vercel | +20 | Modern stack (source maps, API routes) |
| Socket.IO | +15 | Real-time (crash games, timing attacks) |
| Source maps | +15 | Debug info exposed |
| API URLs found | +15 | Hidden endpoints discovered |
| RPC URLs | +10 | Solana node access |
| Program IDs | +15 | On-chain programs referenced |
| Admin routes | +10 | /admin, /debug in JS bundles |

**Classification:**
- **80-100:** `high_priority_for_authorized_followup`
- **60-79:** `interesting_for_authorized_followup`
- **40-59:** `moderate_interest`
- **0-39:** `low_priority`

**Output:** `top3.json`

```json
{
  "top_sites": [
    {
      "site": "https://jup.ag",
      "score": 115,
      "classification": "high_priority_for_authorized_followup",
      "detected_features": [
        "Vercel",
        "Next.js",
        "Solana wallet adapter",
        "API URLs (6)",
        "RPC URLs"
      ],
      "js_analysis": {
        "api_urls": ["https://api.jup.ag/..."],
        "rpc_urls": ["https://solana-mainnet.rpc..."],
        "program_ids": ["JUP4Fb2cqiRUcaTHdrPC8h2gNsA2ETXiPDD33WcGuJB"]
      }
    }
  ]
}
```

**Options:**
- `--input FILE` - Input from Stage 1 (required)
- `--top N` - Number of sites to select (default: 3)
- `--out FILE` - Output file (default: top3.json)

---

## 💀 **STAGE 3: FOX_PROOF_SCANNER**

**What it does:** Active exploitation on top 3 sites

**⚠️  REQUIRES EXPLICIT AUTHORIZATION ⚠️**

**Checks:**

### **Web3-Specific:**
- Solana authority exposure
- Private RPC URL leaks
- Privy auth misconfiguration
- Socket.IO timing attacks (crash games)
- Wallet drainer vectors (XSS + wallet)
- Unlimited token approval risks

### **General Web:**
- XSS, SQLi, SSRF, IDOR, CSRF
- Path traversal, command injection
- `.git`, `.env`, backup file exposure
- JWT attacks, auth bypass
- (All from ULTIMATE_MEGA_SCANNER with zero false positives)

**Output:** `exploitation_report.json`

```json
{
  "scan_type": "active_proof_scanning",
  "results": [
    {
      "target": "https://example.com",
      "total_vulnerabilities": 5,
      "web3_vulnerabilities": [
        {
          "type": "PRIVATE_RPC_URL_EXPOSED",
          "severity": "MEDIUM",
          "evidence": "RPC URL: https://api.mainnet-beta.solana..."
        }
      ],
      "general_vulnerabilities": [...]
    }
  ]
}
```

**Options:**
- `--targets FILE` - Input from Stage 2 (required)
- `--authorized` - Confirm authorization (REQUIRED)
- `--profile TYPE` - Scan profile (optional)
- `--out FILE` - Output file (default: exploitation_report.json)

---

## 🔧 **PIPELINE OPTIONS**

### **RUN_FULL_PIPELINE.sh Flags:**

```bash
--limit N           # Sites to discover (default: 50)
--top N             # Sites to rank (default: 3)
--category TYPE     # Filter: all, solana, defi, crash-game, nft, wallet, bridge
--authorized        # Enable Stage 3 active testing
--skip-stage-3      # Skip active testing (passive only)
```

### **Examples:**

```bash
# Passive intelligence only (safe, no authorization needed)
bash RUN_FULL_PIPELINE.sh --skip-stage-3

# Discover 30 Solana dApps, select top 5
bash RUN_FULL_PIPELINE.sh --limit 30 --top 5 --category solana

# Full exploitation (requires authorization)
bash RUN_FULL_PIPELINE.sh --limit 50 --top 3 --authorized

# Crash games only
bash RUN_FULL_PIPELINE.sh --category crash-game --top 3 --skip-stage-3
```

---

## 📈 **EXAMPLE RUN**

```bash
$ bash RUN_FULL_PIPELINE.sh --limit 30 --top 3 --skip-stage-3
```

**Output:**
```
╔═══════════════════════════════════════════════════════════════════╗
║              💀🔥 3-STAGE WEB3 INTELLIGENCE PIPELINE 🔥💀         ║
╚═══════════════════════════════════════════════════════════════════╝

STAGE 1: WEB3 SITE DISCOVERY
  [✓] Discovered 30 sites → candidates.json

STAGE 2: PASSIVE RISK RANKING
  [✓] Ranked top 3 sites → top3.json

TOP 3 SITES:
  #1. https://jup.ag          Score: 115 (high_priority)
  #2. https://solend.fi        Score: 75  (interesting)
  #3. https://magiceden.io     Score: 75  (interesting)

PIPELINE COMPLETE (Stages 1-2 only)
```

---

## 🎯 **WHAT MAKES THIS DIFFERENT**

### **Other Scanners:**
- Scan everything equally (slow, noisy)
- Report keyword matches as "vulnerabilities"
- 90% false positives
- No Web3-specific checks

### **Fox's Pipeline:**
1. **Smart filtering** - Finds 50 sites, tests top 3 only
2. **Proof required** - No reports without validation
3. **Zero false positives** - Eliminated IDOR/CSRF HTML page bugs
4. **Web3-aware** - Knows Solana program IDs, Privy, crash games
5. **Passive first** - Stage 2 never triggers alerts

---

## 📦 **FILES CREATED**

```
Fox/
├── WEB3_SITE_HUNTER.py          # Stage 1: Discovery
├── PASSIVE_RISK_RANKER.py       # Stage 2: Ranking
├── FOX_PROOF_SCANNER.py         # Stage 3: Exploitation
├── RUN_FULL_PIPELINE.sh         # Orchestrator
├── ULTIMATE_MEGA_SCANNER.py     # Core scanner (fixed)
├── modules/
│   ├── collector.py             # Site collection
│   ├── fingerprinter.py         # Stack detection
│   ├── js_analyzer.py           # JS bundle analysis
│   ├── ranker.py                # Scoring engine
│   └── web3_specific_checks.py  # Web3 exploits
└── output/
    ├── candidates.json          # Stage 1 output
    ├── top3.json                # Stage 2 output
    └── exploitation_report.json # Stage 3 output
```

---

## ⚠️  **LEGAL & ETHICAL USE**

### **You MUST:**
- Have explicit written authorization to test targets
- Understand local laws regarding security testing
- Use `--authorized` flag only when legally authorized
- Never test production systems without permission

### **Passive Intelligence (Stages 1-2):**
- Reads public data only
- No exploitation attempts
- No active probing
- Legal for security research

### **Active Testing (Stage 3):**
- Triggers security alerts
- May violate laws without authorization
- Requires explicit permission
- For authorized penetration testing ONLY

---

## 🔥 **SUMMARY**

**What it is:**
- 3-stage Web3 intelligence pipeline
- Discovers → Scores → Exploits
- Zero false positives
- Built for Solana/DeFi/crash games

**What it's NOT:**
- Not a "scan everything" tool
- Not a keyword matcher
- Not for unauthorized testing
- Not producing 64 fake vulnerabilities

**Use it for:**
- Authorized penetration testing
- Bug bounty hunting
- Security research
- Red team operations

---

**Built by Fox | Partner: Jack | 2026**

💀 No mercy, no survivors, no false positives 💀
