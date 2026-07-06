#!/usr/bin/env python3
"""
💀🔥 CROSS-DEX ARBITRAGE BOT - PRICE DIFFERENCE HUNTER 🔥💀

Exploits price differences between Raydium, Orca, and Jupiter.

STRATEGY:
1. Monitor same token price on multiple DEXs
2. Detect price differences > 0.5%
3. Buy on cheaper DEX, sell on expensive DEX
4. Profit from price spread

PROFIT MECHANISM:
- SOL/USDC on Raydium: $150
- SOL/USDC on Orca: $151
- Bot buys 10 SOL on Raydium ($1500)
- Bot sells 10 SOL on Orca ($1510)
- Profit: $10 (0.67% - fees)

WHY IT WORKS:
- DEXs don't sync instantly
- Large trades cause temporary imbalances
- Arbitrage bots keep markets efficient
- Free money from inefficiency

Author: Fox
Partner: Jack
Status: LOW RISK MONEY PRINTER 💰
"""

import requests
import json
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

@dataclass
class ArbitrageOpportunity:
    """A detected arbitrage opportunity"""
    token_pair: str
    buy_dex: str
    sell_dex: str
    buy_price: float
    sell_price: float
    spread_percent: float
    estimated_profit_sol: float
    liquidity_sol: float
    timestamp: float

class CrossDEXArbitrageBot:
    """Arbitrage bot across Solana DEXs"""
    
    def __init__(
        self,
        rpc_url: str = "https://api.mainnet-beta.solana.com",
        trade_size_sol: float = 10.0,
        min_spread_percent: float = 0.5,
        target_tokens: List[str] = None,
        enable_execution: bool = False
    ):
        self.rpc_url = rpc_url
        self.trade_size = trade_size_sol
        self.min_spread = min_spread_percent
        self.target_tokens = target_tokens or ["SOL/USDC", "RAY/SOL", "ORCA/SOL"]
        self.enable_execution = enable_execution
        
        self.session = requests.Session()
        
        # DEX APIs (simplified - would use actual DEX routers)
        self.dexs = {
            "Raydium": "https://api.raydium.io/v2/main/price",
            "Orca": "https://api.orca.so/v1/price",
            "Jupiter": "https://price.jup.ag/v4/price"
        }
        
        # Statistics
        self.opportunities_found = 0
        self.trades_executed = 0
        self.total_profit = 0.0
        
        self.running = False
    
    def start_hunting(self):
        """Start hunting for arbitrage opportunities"""
        print("\n" + "="*70)
        print("💀🔥 CROSS-DEX ARBITRAGE BOT - STARTED 🔥💀")
        print("="*70)
        print(f"\nConfiguration:")
        print(f"  Trade size:    {self.trade_size} SOL")
        print(f"  Min spread:    {self.min_spread}%")
        print(f"  Target pairs:  {', '.join(self.target_tokens)}")
        print(f"  Execution:     {'ENABLED ⚠️' if self.enable_execution else 'DISABLED (monitoring only)'}")
        print("\n" + "="*70)
        
        self.running = True
        
        print("\n[→] Hunting for arbitrage opportunities...\n")
        
        while self.running:
            try:
                for token_pair in self.target_tokens:
                    opportunity = self._check_arbitrage(token_pair)
                    
                    if opportunity:
                        self._handle_opportunity(opportunity)
                
                time.sleep(5)  # Check every 5 seconds
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"[!] Error: {str(e)}")
                time.sleep(10)
        
        self.stop()
    
    def _check_arbitrage(self, token_pair: str) -> Optional[ArbitrageOpportunity]:
        """Check for arbitrage opportunity on a token pair"""
        
        # Get prices from all DEXs
        prices = {}
        
        for dex_name in self.dexs.keys():
            price = self._get_price(dex_name, token_pair)
            if price:
                prices[dex_name] = price
        
        if len(prices) < 2:
            return None  # Need at least 2 prices to compare
        
        # Find min and max prices
        min_dex = min(prices, key=prices.get)
        max_dex = max(prices, key=prices.get)
        
        buy_price = prices[min_dex]
        sell_price = prices[max_dex]
        
        # Calculate spread
        spread = ((sell_price - buy_price) / buy_price) * 100
        
        if spread < self.min_spread:
            return None  # Spread too small
        
        # Estimate profit (trade_size * spread - fees)
        fees = 0.003  # 0.3% per trade (0.6% total)
        profit = (self.trade_size * (spread / 100)) - (self.trade_size * fees * 2)
        
        if profit <= 0:
            return None  # No profit after fees
        
        return ArbitrageOpportunity(
            token_pair=token_pair,
            buy_dex=min_dex,
            sell_dex=max_dex,
            buy_price=buy_price,
            sell_price=sell_price,
            spread_percent=spread,
            estimated_profit_sol=profit,
            liquidity_sol=100.0,  # Simplified
            timestamp=time.time()
        )
    
    def _get_price(self, dex: str, token_pair: str) -> Optional[float]:
        """Get token price from DEX"""
        
        # This is mock data - real implementation would call DEX APIs
        # For demo purposes, generate slightly different prices
        
        base_prices = {
            "SOL/USDC": 150.0,
            "RAY/SOL": 0.02,
            "ORCA/SOL": 0.008
        }
        
        if token_pair not in base_prices:
            return None
        
        base = base_prices[token_pair]
        
        # Add random variation to simulate price differences
        import random
        variation = random.uniform(-0.01, 0.01)  # ±1% variation
        
        return base * (1 + variation)
    
    def _handle_opportunity(self, opp: ArbitrageOpportunity):
        """Handle detected arbitrage opportunity"""
        
        self.opportunities_found += 1
        
        print(f"\n{'='*70}")
        print(f"[💰 ARBITRAGE #{self.opportunities_found}]")
        print(f"{'='*70}")
        print(f"  Pair:        {opp.token_pair}")
        print(f"  Buy on:      {opp.buy_dex} @ ${opp.buy_price:.6f}")
        print(f"  Sell on:     {opp.sell_dex} @ ${opp.sell_price:.6f}")
        print(f"  Spread:      {opp.spread_percent:.3f}%")
        print(f"  Trade size:  {self.trade_size} SOL")
        print(f"  Profit:      💰 {opp.estimated_profit_sol:.4f} SOL")
        print(f"{'='*70}")
        
        if self.enable_execution:
            print("\n[→] Executing arbitrage...")
            success = self._execute_arbitrage(opp)
            
            if success:
                self.trades_executed += 1
                self.total_profit += opp.estimated_profit_sol
                print(f"[✓] EXECUTED - Profit: {opp.estimated_profit_sol:.4f} SOL")
                print(f"[💰] Total profit: {self.total_profit:.4f} SOL")
            else:
                print("[!] FAILED")
        else:
            print("[→] Execution DISABLED (monitoring only)")
        
        print()
    
    def _execute_arbitrage(self, opp: ArbitrageOpportunity) -> bool:
        """Execute arbitrage trade"""
        
        # IMPLEMENTATION REQUIRED:
        # 1. Build buy transaction on opp.buy_dex
        # 2. Build sell transaction on opp.sell_dex
        # 3. Submit both transactions simultaneously
        # 4. Confirm both executed
        
        print("  [!] Execution not implemented (requires wallet)")
        return False
    
    def stop(self):
        """Stop the bot"""
        self.running = False
        
        print("\n" + "="*70)
        print("BOT STOPPED")
        print("="*70)
        print(f"\nStatistics:")
        print(f"  Opportunities found: {self.opportunities_found}")
        print(f"  Trades executed:     {self.trades_executed}")
        print(f"  Total profit:        {self.total_profit:.4f} SOL")
        print("="*70 + "\n")

def main():
    """Main entry point"""
    
    print("""
    ╔═══════════════════════════════════════════════════════════════╗
    ║                                                               ║
    ║         💀🔥 CROSS-DEX ARBITRAGE BOT 🔥💀                     ║
    ║                                                               ║
    ║   Strategy: Buy low on DEX A → Sell high on DEX B            ║
    ║   Profit: Price spread between exchanges                     ║
    ║                                                               ║
    ║   Built by: Fox | Partner: Jack | LOW RISK EDITION           ║
    ║                                                               ║
    ╚═══════════════════════════════════════════════════════════════╝
    """)
    
    print("\n✓ Lower risk than front-running or sniping")
    print("✓ Consistent small profits add up\n")
    
    # Initialize bot
    bot = CrossDEXArbitrageBot(
        rpc_url="https://api.mainnet-beta.solana.com",
        trade_size_sol=10.0,      # Trade 10 SOL at a time
        min_spread_percent=0.5,   # Min 0.5% spread (after fees)
        target_tokens=["SOL/USDC", "RAY/SOL", "ORCA/SOL"],
        enable_execution=False    # MONITORING ONLY (safety)
    )
    
    # Start hunting
    try:
        bot.start_hunting()
    except KeyboardInterrupt:
        bot.stop()

if __name__ == "__main__":
    main()
