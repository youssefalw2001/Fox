#!/bin/bash
#
# 💀🔥 RUN ALL TRADING BOTS - MONEY PRINTER LAUNCHER 🔥💀
#
# Runs all 4 Solana trading bots simultaneously in background
#
# Usage:
#   ./RUN_ALL_BOTS.sh start    # Start all bots
#   ./RUN_ALL_BOTS.sh stop     # Stop all bots
#   ./RUN_ALL_BOTS.sh status   # Check bot status
#   ./RUN_ALL_BOTS.sh logs     # View all logs
#
# Built by: Fox | Partner: Jack
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Bot list
BOTS=(
    "RAYDIUM_FRONTRUN_BOT.py"
    "SOLANA_SNIPER_BOT.py"
    "ARBITRAGE_BOT.py"
    "WHALE_COPY_BOT.py"
)

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Functions
start_bots() {
    echo -e "${PURPLE}"
    echo "═══════════════════════════════════════════════════════════════"
    echo "          💀🔥 STARTING ALL TRADING BOTS 🔥💀"
    echo "═══════════════════════════════════════════════════════════════"
    echo -e "${NC}"
    
    for bot in "${BOTS[@]}"; do
        if pgrep -f "$bot" > /dev/null; then
            echo -e "${YELLOW}[!] ${bot} already running${NC}"
        else
            echo -e "${GREEN}[→] Starting ${bot}...${NC}"
            nohup python3 -u "$bot" > "${bot%.py}.log" 2>&1 &
            sleep 1
            echo -e "${GREEN}[✓] Started (PID: $!)${NC}"
        fi
    done
    
    echo ""
    echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}[✓] ALL BOTS STARTED - MONEY PRINTER ACTIVATED 💰${NC}"
    echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
    echo ""
    echo -e "${BLUE}View logs:${NC} ./RUN_ALL_BOTS.sh logs"
    echo -e "${BLUE}Check status:${NC} ./RUN_ALL_BOTS.sh status"
    echo ""
}

stop_bots() {
    echo -e "${RED}"
    echo "═══════════════════════════════════════════════════════════════"
    echo "          💀 STOPPING ALL TRADING BOTS 💀"
    echo "═══════════════════════════════════════════════════════════════"
    echo -e "${NC}"
    
    for bot in "${BOTS[@]}"; do
        if pgrep -f "$bot" > /dev/null; then
            echo -e "${YELLOW}[→] Stopping ${bot}...${NC}"
            pkill -f "$bot" || true
            sleep 1
            echo -e "${GREEN}[✓] Stopped${NC}"
        else
            echo -e "${YELLOW}[!] ${bot} not running${NC}"
        fi
    done
    
    echo ""
    echo -e "${RED}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${RED}[✓] ALL BOTS STOPPED${NC}"
    echo -e "${RED}═══════════════════════════════════════════════════════════════${NC}"
    echo ""
}

check_status() {
    echo -e "${BLUE}"
    echo "═══════════════════════════════════════════════════════════════"
    echo "          📊 BOT STATUS CHECK 📊"
    echo "═══════════════════════════════════════════════════════════════"
    echo -e "${NC}"
    
    for bot in "${BOTS[@]}"; do
        if pgrep -f "$bot" > /dev/null; then
            PID=$(pgrep -f "$bot")
            UPTIME=$(ps -p "$PID" -o etime= | tr -d ' ')
            echo -e "${GREEN}[✓] ${bot}${NC}"
            echo -e "    PID: ${PID} | Uptime: ${UPTIME}"
        else
            echo -e "${RED}[✗] ${bot}${NC}"
            echo -e "    Not running"
        fi
        echo ""
    done
    
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
}

view_logs() {
    echo -e "${PURPLE}"
    echo "═══════════════════════════════════════════════════════════════"
    echo "          📋 VIEWING ALL LOGS 📋"
    echo "═══════════════════════════════════════════════════════════════"
    echo -e "${NC}"
    echo ""
    echo -e "${YELLOW}Press Ctrl+C to stop${NC}"
    echo ""
    
    tail -f *.log
}

# Main
case "$1" in
    start)
        start_bots
        ;;
    stop)
        stop_bots
        ;;
    status)
        check_status
        ;;
    logs)
        view_logs
        ;;
    restart)
        stop_bots
        sleep 2
        start_bots
        ;;
    *)
        echo ""
        echo -e "${PURPLE}═══════════════════════════════════════════════════════════════${NC}"
        echo -e "${PURPLE}       💀🔥 TRADING BOTS LAUNCHER 🔥💀${NC}"
        echo -e "${PURPLE}═══════════════════════════════════════════════════════════════${NC}"
        echo ""
        echo "Usage: $0 {start|stop|restart|status|logs}"
        echo ""
        echo "Commands:"
        echo "  start    - Start all bots in background"
        echo "  stop     - Stop all running bots"
        echo "  restart  - Restart all bots"
        echo "  status   - Check which bots are running"
        echo "  logs     - View real-time logs from all bots"
        echo ""
        echo "Bots:"
        for bot in "${BOTS[@]}"; do
            echo "  • ${bot}"
        done
        echo ""
        echo -e "${PURPLE}═══════════════════════════════════════════════════════════════${NC}"
        echo ""
        exit 1
        ;;
esac
