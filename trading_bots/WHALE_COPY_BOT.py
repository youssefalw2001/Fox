#!/usr/bin/env python3
"""
💀🔥 WHALE COPY TRADING BOT - FOLLOW THE MONEY 🔥💀

Monitors whale wallets and copies their trades within seconds.

STRATEGY:
1. Track top 50 Solana whale wallets
2. Monitor their transactions in real-time
3. When whale buys a token, bot buys same token
4. When whale sells, bot sells
5. Profit from whale's market knowledge

PROFIT MECHANISM:
- Whale buys 100 SOL of new token
- Bot detects and buys 1 SOL within 5 seconds
- Whale's buy pumps price 5-20%
- Bot sells at pump
- Profit from whale's influence

WHY IT WORKS:
- Whales have insider info
- Whales move markets
- Following whales = free alpha
- Bot is faster than humans

TOP WHALE WALLETS TO COPY:
- 9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM (Alameda)
- 5Q544fKrFoe6tsEbD7S8EmxGTJYAKtTVhAW5Q5pge4j1 (Jump Trading)
- HBQL7bpxkxjfgxw8LwDd4C3dkVXMZVWLxEQBdz7jMQvn (3AC)

Author: Fox
Partner: Jack
Status: ALPHA HUNTER 💰
"""

import requests
import json
import time
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime

@dataclass
class WhaleTransaction:
    """A whale transaction to copy"""
    whale_wallet: str
    whale_name: str
    action: str  # "BUY" or "SELL"
    token: str
    amount_sol: float
    signature: str
    slot: int
    timestamp: float

class WhaleCopyBot:
    """Bot that copies whale wallet trades"""
    
    def __init__(
        self,
        rpc_url: str = "https://api.mainnet-beta.solana.com",
        whale_wallets: Dict[str, str] = None,
        copy_amount_sol: float = 1.0,
        copy_ratio: float = 0.01,  # Copy 1% of whale's trade size
        enable_execution: bool = False
    ):
        self.rpc_url = rpc_url
        self.whale_wallets = whale_wallets or self._default_whales()
        self.copy_amount = copy_amount_sol
        self.copy_ratio = copy_ratio
        self.enable_execution = enable_execution
        
        self.session = requests.Session()
        
        # Statistics
        self.whale_trades_detected = 0
        self.trades_copied = 0
        self.total_profit = 0.0
        
        # Track last processed signatures per whale
        self.last_signatures = {wallet: None for wallet in self.whale_wallets.keys()}
        
        self.running = False
    
    def _default_whales(self) -> Dict[str, str]:
        """Default whale wallets to monitor"""
        return {
            "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM": "Alameda Research",
            "5Q544fKrFoe6tsEbD7S8EmxGTJYAKtTVhAW5Q5pge4j1": "Jump Trading",
            "HBQL7bpxkxjfgxw8LwDd4C3dkVXMZVWLxEQBdz7jMQvn": "Three Arrows Capital",
            "GqFJgksQDxN7AMNxiGg1MMwrYwz1A9H4MZcKkGKEWqSi": "FTX Hot Wallet",
            "2ojv9BAiHUrvsm9gxDe7fJSzbNZSJcxZvf8dqmWGHG8S": "Binance",
        }
    
    def start_copying(self):
        """Start copying whale trades"""
        print("\n" + "="*70)
        print("💀🔥 WHALE COPY TRADING BOT - STARTED 🔥💀")
        print("="*70)
        print(f"\nConfiguration:")
        print(f"  Monitoring whales: {len(self.whale_wallets)}")
        print(f"  Copy amount:       {self.copy_amount} SOL")
        print(f"  Copy ratio:        {self.copy_ratio * 100}% of whale size")
        print(f"  Execution:         {'ENABLED ⚠️' if self.enable_execution else 'DISABLED (monitoring only)'}")
        
        print(f"\n  Whales tracked:")
        for wallet, name in self.whale_wallets.items():
            print(f"    • {name} ({wallet[:8]}...)")
        
        print("\n" + "="*70)
        
        self.running = True
        
        print("\n[→] Monitoring whale wallets...\n")
        
        while self.running:
            try:
                for wallet, name in self.whale_wallets.items():
                    # Get recent transactions
                    transactions = self._get_whale_transactions(wallet)
                    
                    for tx in transactions:
                        # Skip if already processed
                        if tx['signature'] == self.last_signatures[wallet]:
                            break
                        
                        # Analyze transaction
                        whale_trade = self._analyze_transaction(wallet, name, tx)
                        
                        if whale_trade:
                            self._handle_whale_trade(whale_trade)
                    
                    # Update last signature
                    if transactions:
                        self.last_signatures[wallet] = transactions[0]['signature']
                
                time.sleep(3)  # Check every 3 seconds
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"[!] Error: {str(e)}")
                time.sleep(10)
        
        self.stop()
    
    def _get_whale_transactions(self, wallet: str) -> List[Dict]:
        """Get recent transactions for whale wallet"""
        try:
            response = self.session.post(
                self.rpc_url,
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "getSignaturesForAddress",
                    "params": [wallet, {"limit": 10}]
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get('result', [])
        except:
            pass
        
        return []
    
    def _analyze_transaction(self, wallet: str, name: str, tx_info: Dict) -> Optional[WhaleTransaction]:
        """Analyze whale transaction to determine if it's a trade to copy"""
        
        # Skip failed transactions
        if tx_info.get('err'):
            return None
        
        signature = tx_info['signature']
        
        # Get full transaction details
        tx_data = self._get_transaction_details(signature)
        
        if not tx_data:
            return None
        
        # Parse for token swap
        trade_info = self._parse_swap(tx_data)
        
        if not trade_info:
            return None
        
        # Check if trade is significant enough to copy
        if trade_info['amount_sol'] < 5.0:
            return None  # Ignore small trades
        
        return WhaleTransaction(
            whale_wallet=wallet,
            whale_name=name,
            action=trade_info['action'],
            token=trade_info['token'],
            amount_sol=trade_info['amount_sol'],
            signature=signature,
            slot=tx_info['slot'],
            timestamp=time.time()
        )
    
    def _get_transaction_details(self, signature: str) -> Optional[Dict]:
        """Get transaction details"""
        try:
            response = self.session.post(
                self.rpc_url,
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "getTransaction",
                    "params": [
                        signature,
                        {"encoding": "json", "maxSupportedTransactionVersion": 0}
                    ]
                },
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get('result')
        except:
            pass
        
        return None
    
    def _parse_swap(self, tx_data: Dict) -> Optional[Dict]:
        """Parse transaction to extract swap details"""
        
        meta = tx_data.get('meta', {})
        
        # Get balance changes
        pre_balances = meta.get('preBalances', [])
        post_balances = meta.get('postBalances', [])
        
        if not pre_balances or not post_balances:
            return None
        
        # Calculate SOL change (simplified)
        sol_change = (post_balances[0] - pre_balances[0]) / 1e9
        
        if abs(sol_change) < 0.01:
            return None
        
        # Determine action
        action = "BUY" if sol_change < 0 else "SELL"
        
        return {
            'action': action,
            'token': 'TOKEN',  # Simplified
            'amount_sol': abs(sol_change)
        }
    
    def _handle_whale_trade(self, whale_trade: WhaleTransaction):
        """Handle detected whale trade"""
        
        self.whale_trades_detected += 1
        
        print(f"\n{'='*70}")
        print(f"[🐋 WHALE TRADE #{self.whale_trades_detected}]")
        print(f"{'='*70}")
        print(f"  Whale:       {whale_trade.whale_name}")
        print(f"  Wallet:      {whale_trade.whale_wallet[:20]}...")
        print(f"  Action:      {whale_trade.action}")
        print(f"  Token:       {whale_trade.token}")
        print(f"  Amount:      {whale_trade.amount_sol:.2f} SOL")
        print(f"  Signature:   {whale_trade.signature[:30]}...")
        print(f"  Time:        {datetime.fromtimestamp(whale_trade.timestamp).strftime('%H:%M:%S')}")
        print(f"{'='*70}")
        
        # Calculate copy amount
        copy_amount = min(
            self.copy_amount,
            whale_trade.amount_sol * self.copy_ratio
        )
        
        print(f"\n  [→] Copying trade: {whale_trade.action} {copy_amount:.4f} SOL")
        
        if self.enable_execution:
            print(f"  [→] Executing {whale_trade.action}...")
            success = self._execute_copy(whale_trade, copy_amount)
            
            if success:
                self.trades_copied += 1
                print(f"  [✓] COPIED - Trade executed")
            else:
                print(f"  [!] FAILED")
        else:
            print("  [→] Execution DISABLED (monitoring only)")
        
        print()
    
    def _execute_copy(self, whale_trade: WhaleTransaction, amount: float) -> bool:
        """Execute copy trade"""
        
        # IMPLEMENTATION REQUIRED:
        # 1. If whale_trade.action == "BUY":
        #      - Build swap: SOL → whale_trade.token
        #      - Amount: amount SOL
        # 2. If whale_trade.action == "SELL":
        #      - Build swap: whale_trade.token → SOL
        # 3. Sign and submit transaction
        
        print("    [!] Execution not implemented (requires wallet)")
        return False
    
    def stop(self):
        """Stop the bot"""
        self.running = False
        
        print("\n" + "="*70)
        print("BOT STOPPED")
        print("="*70)
        print(f"\nStatistics:")
        print(f"  Whale trades detected: {self.whale_trades_detected}")
        print(f"  Trades copied:         {self.trades_copied}")
        print(f"  Total profit:          {self.total_profit:.4f} SOL")
        print("="*70 + "\n")

def main():
    """Main entry point"""
    
    print("""
    ╔═══════════════════════════════════════════════════════════════╗
    ║                                                               ║
    ║         💀🔥 WHALE COPY TRADING BOT 🔥💀                      ║
    ║                                                               ║
    ║   Strategy: Monitor whale wallets → Copy their trades        ║
    ║   Profit: Whale's market influence + insider knowledge       ║
    ║                                                               ║
    ║   Built by: Fox | Partner: Jack | ALPHA HUNTER EDITION       ║
    ║                                                               ║
    ╚═══════════════════════════════════════════════════════════════╝
    """)
    
    print("\n✓ Follow the smart money")
    print("✓ Whales have insider info")
    print("✓ Free alpha from monitoring\n")
    
    # Initialize bot
    bot = WhaleCopyBot(
        rpc_url="https://api.mainnet-beta.solana.com",
        copy_amount_sol=1.0,   # Copy with 1 SOL
        copy_ratio=0.01,       # Or 1% of whale's size (whichever is less)
        enable_execution=False  # MONITORING ONLY (safety)
    )
    
    # Start copying
    try:
        bot.start_copying()
    except KeyboardInterrupt:
        bot.stop()

if __name__ == "__main__":
    main()
