#!/usr/bin/env python3
"""
💀🔥 STACK FINGERPRINTER - FOX'S TECH DETECTION ENGINE 🔥💀

Detects Web3 tech stack from public homepage/resources.
No active exploitation - just passive fingerprinting.
"""

import requests
import re
from typing import Dict, List, Set
from urllib.parse import urlparse

class StackFingerprinter:
    """Detects Web3 technology stack from public resources"""
    
    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Web3 Research Bot)'
        })
    
    def fingerprint_site(self, url: str) -> Dict:
        """Fingerprint a single site's tech stack"""
        result = {
            "site": url,
            "reachable": False,
            "technologies": [],
            "frameworks": [],
            "web3_indicators": [],
            "js_files": [],
            "score_components": {}
        }
        
        try:
            # Fetch homepage
            r = self.session.get(url, timeout=self.timeout, allow_redirects=True)
            result["reachable"] = True
            result["status_code"] = r.status_code
            
            if r.status_code != 200:
                return result
            
            html = r.text
            headers = dict(r.headers)
            
            # Detect server/CDN
            server = headers.get('server', '').lower()
            if 'cloudflare' in server or 'cf-ray' in headers:
                result["technologies"].append("Cloudflare")
                result["score_components"]["cloudflare"] = 5
            
            if 'vercel' in server or 'x-vercel-id' in headers:
                result["technologies"].append("Vercel")
                result["frameworks"].append("Next.js")
                result["score_components"]["vercel"] = 20
            
            # Detect React
            if 'react' in html.lower() or '__NEXT_DATA__' in html or '_app-' in html:
                result["frameworks"].append("React")
                result["score_components"]["react"] = 10
            
            # Detect Next.js
            if '__NEXT_DATA__' in html or '_next/static' in html or 'next.js' in html.lower():
                result["frameworks"].append("Next.js")
                result["score_components"]["nextjs"] = 20
            
            # Detect Solana wallet adapter
            if any(x in html.lower() for x in ['solana/wallet-adapter', '@solana/web3', 'wallet-adapter', 'solana-labs']):
                result["web3_indicators"].append("Solana-Wallet-Adapter")
                result["score_components"]["solana_wallet"] = 25
            
            # Detect Privy
            if 'privy' in html.lower() or 'privy.io' in html.lower():
                result["web3_indicators"].append("Privy")
                result["score_components"]["privy"] = 20
            
            # Detect Phantom
            if 'phantom' in html.lower():
                result["web3_indicators"].append("Phantom")
                result["score_components"]["phantom"] = 10
            
            # Detect Socket.IO
            if 'socket.io' in html.lower() or '/socket.io/' in html:
                result["technologies"].append("Socket.IO")
                result["score_components"]["socketio"] = 15
            
            # Detect WebSocket usage
            if 'websocket' in html.lower() or 'ws://' in html or 'wss://' in html:
                result["technologies"].append("WebSocket")
                result["score_components"]["websocket"] = 10
            
            # Detect source maps
            if '.map' in html and ('//# sourceMappingURL=' in html or 'sourceMap' in html):
                result["technologies"].append("SourceMaps")
                result["score_components"]["sourcemaps"] = 15
            
            # Detect GraphQL
            if 'graphql' in html.lower() or '/graphql' in html:
                result["technologies"].append("GraphQL")
                result["score_components"]["graphql"] = 5
            
            # Extract JS file references
            js_pattern = r'(?:src|href)=["\']([^"\']+\.js[^"\']*)["\'"]'
            js_files = re.findall(js_pattern, html)
            result["js_files"] = list(set(js_files))[:20]  # Top 20 unique
            
            if len(result["js_files"]) > 10:
                result["score_components"]["many_js_files"] = 5
            
            # Detect admin/debug strings
            if any(x in html.lower() for x in ['admin', 'debug', '/api/admin', '/api/debug', 'devtools']):
                result["technologies"].append("Admin-Debug-Routes")
                result["score_components"]["admin_routes"] = 10
            
            # Detect crash game indicators
            if any(x in html.lower() for x in ['serverseedhash', 'clientseed', 'multiplier', 'crash', 'provably fair']):
                result["web3_indicators"].append("Crash-Game-Indicators")
                result["score_components"]["crash_game"] = 10
            
            # Detect Anchor (Solana framework)
            if 'anchor' in html.lower() or '@project-serum' in html.lower():
                result["web3_indicators"].append("Anchor")
                result["score_components"]["anchor"] = 15
            
        except requests.Timeout:
            result["error"] = "timeout"
        except requests.ConnectionError:
            result["error"] = "connection_failed"
        except Exception as e:
            result["error"] = str(e)[:100]
        
        return result
