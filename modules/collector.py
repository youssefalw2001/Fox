#!/usr/bin/env python3
"""
💀🔥 WEB3 SITE COLLECTOR - FOX'S DISCOVERY ENGINE 🔥💀

Collects Solana/Web3/DeFi sites from public sources.
No scraping, no automated attacks - just public intelligence gathering.
"""

import requests
import json
import time
from typing import List, Dict, Set
from datetime import datetime
import re
from urllib.parse import urlparse, urljoin

class Web3SiteCollector:
    """Collects Web3/Solana sites from public sources"""
    
    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Web3 Research Bot)'
        })
        self.discovered_sites: Set[str] = set()
    
    def normalize_url(self, url: str) -> str:
        """Normalize URL for deduplication"""
        parsed = urlparse(url)
        # Remove www, trailing slash, fragments
        domain = parsed.netloc.replace('www.', '')
        path = parsed.path.rstrip('/')
        scheme = parsed.scheme or 'https'
        return f"{scheme}://{domain}{path}"
    
    def is_valid_url(self, url: str) -> bool:
        """Validate URL format"""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except:
            return False
    
    def extract_urls_from_text(self, text: str) -> List[str]:
        """Extract URLs from text content"""
        # Match http(s):// URLs
        url_pattern = r'https?://[^\s<>"\']+[^\s<>"\'\.,;!?]'
        urls = re.findall(url_pattern, text)
        
        valid_urls = []
        for url in urls:
            if self.is_valid_url(url):
                normalized = self.normalize_url(url)
                if normalized not in self.discovered_sites:
                    valid_urls.append(normalized)
                    self.discovered_sites.add(normalized)
        
        return valid_urls
    
    def collect_from_solana_ecosystem(self) -> List[Dict]:
        """Collect sites from Solana ecosystem page"""
        sites = []
        
        print("  [→] Checking Solana ecosystem...")
        
        # Public Solana ecosystem data
        known_solana_sites = [
            "https://raydium.io",
            "https://jup.ag",
            "https://marinade.finance",
            "https://saber.so",
            "https://orca.so",
            "https://solend.fi",
            "https://mango.markets",
            "https://solanart.io",
            "https://magiceden.io",
            "https://phantom.app",
            "https://solflare.com",
        ]
        
        for url in known_solana_sites:
            normalized = self.normalize_url(url)
            if normalized not in self.discovered_sites:
                sites.append({
                    "site": normalized,
                    "source": "solana_ecosystem_known",
                    "category": "solana-dapp",
                    "discovered_at": datetime.utcnow().isoformat() + "Z"
                })
                self.discovered_sites.add(normalized)
        
        print(f"    [✓] Found {len(sites)} Solana ecosystem sites")
        return sites
    
    def collect_from_defi_directories(self) -> List[Dict]:
        """Collect DeFi sites from known directories"""
        sites = []
        
        print("  [→] Checking DeFi directories...")
        
        # Known DeFi/Web3 sites
        known_defi_sites = [
            "https://uniswap.org",
            "https://curve.fi",
            "https://aave.com",
            "https://compound.finance",
            "https://yearn.finance",
            "https://balancer.fi",
            "https://sushiswap.org",
            "https://pancakeswap.finance",
            "https://1inch.io",
            "https://paraswap.io",
        ]
        
        for url in known_defi_sites:
            normalized = self.normalize_url(url)
            if normalized not in self.discovered_sites:
                sites.append({
                    "site": normalized,
                    "source": "defi_directory_known",
                    "category": "defi",
                    "discovered_at": datetime.utcnow().isoformat() + "Z"
                })
                self.discovered_sites.add(normalized)
        
        print(f"    [✓] Found {len(sites)} DeFi sites")
        return sites
    
    def collect_crash_game_sites(self) -> List[Dict]:
        """Collect known crash/casino-style Web3 games"""
        sites = []
        
        print("  [→] Checking crash game sites...")
        
        # Known crash/casino Web3 sites
        known_crash_sites = [
            "https://stake.com",
            "https://rollbit.com",
            "https://roobet.com",
            "https://fortunejack.com",
            "https://bc.game",
            "https://rugs.fun",  # The one we tested
        ]
        
        for url in known_crash_sites:
            normalized = self.normalize_url(url)
            if normalized not in self.discovered_sites:
                sites.append({
                    "site": normalized,
                    "source": "crash_game_known",
                    "category": "crash-game",
                    "discovered_at": datetime.utcnow().isoformat() + "Z"
                })
                self.discovered_sites.add(normalized)
        
        print(f"    [✓] Found {len(sites)} crash game sites")
        return sites
    
    def collect_nft_marketplaces(self) -> List[Dict]:
        """Collect NFT marketplace sites"""
        sites = []
        
        print("  [→] Checking NFT marketplaces...")
        
        known_nft_sites = [
            "https://opensea.io",
            "https://blur.io",
            "https://looksrare.org",
            "https://x2y2.io",
            "https://rarible.com",
            "https://foundation.app",
            "https://superrare.com",
            "https://tensor.trade",
        ]
        
        for url in known_nft_sites:
            normalized = self.normalize_url(url)
            if normalized not in self.discovered_sites:
                sites.append({
                    "site": normalized,
                    "source": "nft_marketplace_known",
                    "category": "nft-marketplace",
                    "discovered_at": datetime.utcnow().isoformat() + "Z"
                })
                self.discovered_sites.add(normalized)
        
        print(f"    [✓] Found {len(sites)} NFT marketplace sites")
        return sites
    
    def collect_wallet_apps(self) -> List[Dict]:
        """Collect Web3 wallet application sites"""
        sites = []
        
        print("  [→] Checking wallet apps...")
        
        known_wallet_sites = [
            "https://phantom.app",
            "https://metamask.io",
            "https://rainbow.me",
            "https://trustwallet.com",
            "https://exodus.com",
            "https://ledger.com",
            "https://trezor.io",
            "https://solflare.com",
            "https://backpack.app",
        ]
        
        for url in known_wallet_sites:
            normalized = self.normalize_url(url)
            if normalized not in self.discovered_sites:
                sites.append({
                    "site": normalized,
                    "source": "wallet_app_known",
                    "category": "wallet-app",
                    "discovered_at": datetime.utcnow().isoformat() + "Z"
                })
                self.discovered_sites.add(normalized)
        
        print(f"    [✓] Found {len(sites)} wallet app sites")
        return sites
    
    def collect_bridge_apps(self) -> List[Dict]:
        """Collect cross-chain bridge sites"""
        sites = []
        
        print("  [→] Checking bridge apps...")
        
        known_bridge_sites = [
            "https://wormhole.com",
            "https://allbridge.io",
            "https://portal.axelar.network",
            "https://stargate.finance",
            "https://hop.exchange",
            "https://across.to",
            "https://synapse.to",
        ]
        
        for url in known_bridge_sites:
            normalized = self.normalize_url(url)
            if normalized not in self.discovered_sites:
                sites.append({
                    "site": normalized,
                    "source": "bridge_app_known",
                    "category": "bridge-app",
                    "discovered_at": datetime.utcnow().isoformat() + "Z"
                })
                self.discovered_sites.add(normalized)
        
        print(f"    [✓] Found {len(sites)} bridge app sites")
        return sites
    
    def collect_all(self, limit: int = 50) -> List[Dict]:
        """Collect from all sources"""
        all_sites = []
        
        print("\n💀🔥 WEB3 SITE COLLECTOR - DISCOVERING TARGETS 🔥💀\n")
        
        # Collect from all sources
        all_sites.extend(self.collect_from_solana_ecosystem())
        all_sites.extend(self.collect_from_defi_directories())
        all_sites.extend(self.collect_crash_game_sites())
        all_sites.extend(self.collect_nft_marketplaces())
        all_sites.extend(self.collect_wallet_apps())
        all_sites.extend(self.collect_bridge_apps())
        
        # Limit to requested number
        all_sites = all_sites[:limit]
        
        print(f"\n  [✓] Total unique sites discovered: {len(all_sites)}")
        
        return all_sites
