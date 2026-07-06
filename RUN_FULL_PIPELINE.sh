#!/bin/bash
###############################################################################
# 💀🔥 FOX'S 3-STAGE WEB3 INTELLIGENCE PIPELINE 🔥💀
#
# Full automation: Discovery → Passive Ranking → Active Proof Scanning
#
# Author: Fox
# Partner: Jack
#
# USAGE:
#   bash RUN_FULL_PIPELINE.sh
#   bash RUN_FULL_PIPELINE.sh --limit 30 --top 5
#   bash RUN_FULL_PIPELINE.sh --category solana --authorized
###############################################################################

set -e  # Exit on error

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Default parameters
LIMIT=50
TOP=3
CATEGORY="all"
AUTHORIZED=""
SKIP_STAGE_3=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --limit)
            LIMIT="$2"
            shift 2
            ;;
        --top)
            TOP="$2"
            shift 2
            ;;
        --category)
            CATEGORY="$2"
            shift 2
            ;;
        --authorized)
            AUTHORIZED="--authorized"
            shift
            ;;
        --skip-stage-3)
            SKIP_STAGE_3=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Banner
echo -e "${PURPLE}"
cat << "EOF"
╔═══════════════════════════════════════════════════════════════════╗
║                                                                   ║
║   ███████╗ ██████╗ ██╗  ██╗    ██████╗ ██╗██████╗ ███████╗██╗    ██╗███╗   ██╗███████╗  ║
║   ██╔════╝██╔═══██╗╚██╗██╔╝    ██╔══██╗██║██╔══██╗██╔════╝██║    ██║████╗  ██║██╔════╝  ║
║   █████╗  ██║   ██║ ╚███╔╝     ██████╔╝██║██████╔╝█████╗  ██║    ██║██╔██╗ ██║█████╗    ║
║   ██╔══╝  ██║   ██║ ██╔██╗     ██╔═══╝ ██║██╔═══╝ ██╔══╝  ██║    ██║██║╚██╗██║██╔══╝    ║
║   ██║     ╚██████╔╝██╔╝ ██╗    ██║     ██║██║     ███████╗███████╗██║██║ ╚████║███████╗  ║
║   ╚═╝      ╚═════╝ ╚═╝  ╚═╝    ╚═╝     ╚═╝╚═╝     ╚══════╝╚══════╝╚═╝╚═╝  ╚═══╝╚══════╝  ║
║                                                                   ║
║              💀🔥 3-STAGE WEB3 INTELLIGENCE PIPELINE 🔥💀         ║
║                                                                   ║
║   Stage 1: Discovery  →  Stage 2: Ranking  →  Stage 3: Exploit  ║
║                                                                   ║
╚═══════════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

echo -e "${CYAN}═══════════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}PIPELINE CONFIGURATION${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════════════${NC}"
echo -e "  Sites to discover:  ${GREEN}${LIMIT}${NC}"
echo -e "  Category filter:    ${GREEN}${CATEGORY}${NC}"
echo -e "  Top sites to rank:  ${GREEN}${TOP}${NC}"
echo -e "  Stage 3 authorized: ${GREEN}${AUTHORIZED:-NO}${NC}"
if [ "$SKIP_STAGE_3" = true ]; then
    echo -e "  Stage 3:            ${YELLOW}SKIPPED${NC}"
fi
echo -e "${CYAN}═══════════════════════════════════════════════════════════════════${NC}"
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}[!] Python 3 not found${NC}"
    exit 1
fi

# Install dependencies if needed
echo -e "${BLUE}[→] Checking dependencies...${NC}"
if ! python3 -c "import tqdm" 2>/dev/null; then
    echo -e "${YELLOW}[→] Installing tqdm...${NC}"
    pip3 install tqdm -q
fi
echo -e "${GREEN}[✓] Dependencies OK${NC}"
echo ""

# Stage 1: Discovery
echo -e "${PURPLE}═══════════════════════════════════════════════════════════════════${NC}"
echo -e "${PURPLE}STAGE 1: WEB3 SITE DISCOVERY${NC}"
echo -e "${PURPLE}═══════════════════════════════════════════════════════════════════${NC}"
echo ""

python3 WEB3_SITE_HUNTER.py --limit ${LIMIT} --category ${CATEGORY} --out candidates.json

if [ ! -f "candidates.json" ]; then
    echo -e "${RED}[!] Stage 1 failed: candidates.json not created${NC}"
    exit 1
fi

DISCOVERED=$(python3 -c "import json; data=json.load(open('candidates.json')); print(data['total_sites'])")
echo -e "${GREEN}[✓] Stage 1 complete: ${DISCOVERED} sites discovered${NC}"
echo ""

# Stage 2: Passive Ranking
echo -e "${PURPLE}═══════════════════════════════════════════════════════════════════${NC}"
echo -e "${PURPLE}STAGE 2: PASSIVE RISK RANKING${NC}"
echo -e "${PURPLE}═══════════════════════════════════════════════════════════════════${NC}"
echo ""

python3 PASSIVE_RISK_RANKER.py --input candidates.json --top ${TOP} --out top3.json

if [ ! -f "top3.json" ]; then
    echo -e "${RED}[!] Stage 2 failed: top3.json not created${NC}"
    exit 1
fi

RANKED=$(python3 -c "import json; data=json.load(open('top3.json')); print(len(data['top_sites']))")
echo -e "${GREEN}[✓] Stage 2 complete: Top ${RANKED} sites selected${NC}"
echo ""

# Stage 3: Active Proof Scanning (conditional)
if [ "$SKIP_STAGE_3" = true ]; then
    echo -e "${YELLOW}[→] Stage 3 skipped (--skip-stage-3 flag)${NC}"
    echo ""
    echo -e "${CYAN}═══════════════════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}PIPELINE COMPLETE (Stages 1-2 only)${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════════════════${NC}"
    echo -e "  Discovered:  ${GREEN}${DISCOVERED} sites${NC}"
    echo -e "  Ranked:      ${GREEN}${RANKED} sites${NC}"
    echo -e "  Output:      ${GREEN}top3.json${NC}"
    echo ""
    echo -e "${YELLOW}To run Stage 3 (active testing):${NC}"
    echo -e "  bash RUN_FULL_PIPELINE.sh --authorized"
    echo -e "${CYAN}═══════════════════════════════════════════════════════════════════${NC}"
    exit 0
fi

if [ -z "$AUTHORIZED" ]; then
    echo -e "${YELLOW}═══════════════════════════════════════════════════════════════════${NC}"
    echo -e "${YELLOW}⚠️  STAGE 3 REQUIRES AUTHORIZATION ⚠️${NC}"
    echo -e "${YELLOW}═══════════════════════════════════════════════════════════════════${NC}"
    echo ""
    echo -e "Stage 3 performs ${RED}ACTIVE EXPLOITATION${NC} which may:"
    echo -e "  • Trigger security alerts"
    echo -e "  • Be detected by WAF/IDS"
    echo -e "  • Have legal implications"
    echo ""
    echo -e "You must have ${GREEN}explicit written authorization${NC} to test these targets."
    echo ""
    echo -e "To run Stage 3:"
    echo -e "  ${GREEN}bash RUN_FULL_PIPELINE.sh --authorized${NC}"
    echo ""
    echo -e "${YELLOW}═══════════════════════════════════════════════════════════════════${NC}"
    echo ""
    echo -e "${GREEN}[✓] Stages 1-2 complete. Top sites saved to top3.json${NC}"
    exit 0
fi

echo -e "${PURPLE}═══════════════════════════════════════════════════════════════════${NC}"
echo -e "${PURPLE}STAGE 3: ACTIVE PROOF SCANNING${NC}"
echo -e "${PURPLE}═══════════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${RED}⚠️  AUTHORIZED ACTIVE TESTING ENABLED ⚠️${NC}"
echo ""

python3 FOX_PROOF_SCANNER.py --targets top3.json ${AUTHORIZED} --out exploitation_report.json

if [ ! -f "exploitation_report.json" ]; then
    echo -e "${RED}[!] Stage 3 failed: exploitation_report.json not created${NC}"
    exit 1
fi

echo -e "${GREEN}[✓] Stage 3 complete${NC}"
echo ""

# Final summary
echo -e "${PURPLE}═══════════════════════════════════════════════════════════════════${NC}"
echo -e "${PURPLE}3-STAGE PIPELINE COMPLETE${NC}"
echo -e "${PURPLE}═══════════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${GREEN}[✓] Stage 1: Discovered ${DISCOVERED} sites → candidates.json${NC}"
echo -e "${GREEN}[✓] Stage 2: Ranked top ${RANKED} sites → top3.json${NC}"
echo -e "${GREEN}[✓] Stage 3: Active scanning complete → exploitation_report.json${NC}"
echo ""

# Count vulnerabilities
TOTAL_VULNS=$(python3 -c "import json; data=json.load(open('exploitation_report.json')); print(sum(r['total_vulnerabilities'] for r in data['results']))" 2>/dev/null || echo "0")
echo -e "${CYAN}Total vulnerabilities found: ${GREEN}${TOTAL_VULNS}${NC}"
echo ""
echo -e "${PURPLE}═══════════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${GREEN}💀 All 3 stages complete. Review exploitation_report.json for findings.${NC}"
echo ""
