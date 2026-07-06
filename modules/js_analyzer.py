#!/usr/bin/env python3
"""
💀🔥 JAVASCRIPT ANALYZER - FOX'S JS INTELLIGENCE ENGINE 🔥💀

Analyzes public JavaScript bundles for API URLs, RPC endpoints, program IDs.
No exploitation - just passive intelligence gathering.
"""

import requests
import re
from typing import Dict, List, Set
from urllib.parse import urljoin, urlparse

class JSAnalyzer:
    """Analyzes JavaScript files for sensitive information"""
    
    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Web3 Research Bot)'
        })
    
    def analyze_js_files(self, base_url: str, js_files: List[str]) -> Dict:
        """Analyze JS files from a site"""
        result = {
            "analyzed_files": 0,
            "api_urls": [],
            "rpc_urls": [],
            "websocket_urls": [],
            "program_ids": [],
            "api_keys_found": [],
            "admin_routes": [],
            "score_components": {}
        }
        
        # Limit to first 5 JS files (avoid massive downloads)
        js_files_to_check = js_files[:5]
        
        for js_file in js_files_to_check:
            try:
                # Build full URL
                if js_file.startswith('http'):
                    url = js_file
                elif js_file.startswith('//'):
                    url = 'https:' + js_file
                else:
                    url = urljoin(base_url, js_file)
                
                # Fetch JS file
                r = self.session.get(url, timeout=self.timeout)
                
                if r.status_code != 200:
                    continue
                
                js_content = r.text
                result["analyzed_files"] += 1
                
                # Extract API URLs
                api_patterns = [
                    r'(?:apiUrl|API_URL|baseURL|BASE_URL)["\']?\s*[:=]\s*["\']([^"\']+)["\']',
                    r'(?:endpoint|ENDPOINT)["\']?\s*[:=]\s*["\']([^"\']+)["\']',
                    r'https?://[^/]+/api/[^\s"\'<>]+',
                ]
                
                for pattern in api_patterns:
                    matches = re.findall(pattern, js_content, re.IGNORECASE)
                    for match in matches:
                        if match and match.startswith('http'):
                            result["api_urls"].append(match)
                
                # Extract RPC URLs (Solana/Ethereum)
                rpc_patterns = [
                    r'(?:rpcUrl|RPC_URL|rpcEndpoint)["\']?\s*[:=]\s*["\']([^"\']+)["\']',
                    r'https?://[^/]*(?:rpc|node)[^/]*\.(?:com|io|org)[^\s"\'<>]*',
                    r'https?://[^/]*(?:solana|ethereum|polygon)[^/]*[^\s"\'<>]*',
                ]
                
                for pattern in rpc_patterns:
                    matches = re.findall(pattern, js_content, re.IGNORECASE)
                    for match in matches:
                        if match and match.startswith('http'):
                            result["rpc_urls"].append(match)
                
                # Extract WebSocket URLs
                ws_patterns = [
                    r'wss?://[^\s"\'<>]+',
                    r'(?:wsUrl|WS_URL|websocketUrl)["\']?\s*[:=]\s*["\']([^"\']+)["\']',
                ]
                
                for pattern in ws_patterns:
                    matches = re.findall(pattern, js_content)
                    result["websocket_urls"].extend(matches)
                
                # Extract Solana Program IDs (base58 44-char strings)
                program_id_pattern = r'[1-9A-HJ-NP-Za-km-z]{43,44}'
                potential_program_ids = re.findall(program_id_pattern, js_content)
                
                # Filter likely program IDs (start with common prefixes)
                for pid in potential_program_ids:
                    if len(pid) == 44 and any(pid.startswith(prefix) for prefix in ['11', 'So1', 'Token', 'AToken', 'Sysvar']):
                        result["program_ids"].append(pid)
                
                # Look for admin/debug routes
                admin_patterns = [
                    r'/api/admin[^\s"\'<>]*',
                    r'/api/debug[^\s"\'<>]*',
                    r'/api/internal[^\s"\'<>]*',
                    r'/admin[^\s"\'<>]*',
                ]
                
                for pattern in admin_patterns:
                    matches = re.findall(pattern, js_content, re.IGNORECASE)
                    result["admin_routes"].extend(matches)
                
                # Look for potential API keys (NOT validated, just flagged)
                key_patterns = [
                    r'(?:api[_-]?key|apikey|API_KEY)["\']?\s*[:=]\s*["\']([A-Za-z0-9_-]{20,})["\']',
                ]
                
                for pattern in key_patterns:
                    matches = re.findall(pattern, js_content, re.IGNORECASE)
                    result["api_keys_found"].extend(matches)
                
            except:
                continue
        
        # Deduplicate
        result["api_urls"] = list(set(result["api_urls"]))[:10]
        result["rpc_urls"] = list(set(result["rpc_urls"]))[:5]
        result["websocket_urls"] = list(set(result["websocket_urls"]))[:5]
        result["program_ids"] = list(set(result["program_ids"]))[:10]
        result["admin_routes"] = list(set(result["admin_routes"]))[:10]
        result["api_keys_found"] = list(set(result["api_keys_found"]))[:5]
        
        # Score components
        if result["api_urls"]:
            result["score_components"]["api_urls"] = min(len(result["api_urls"]) * 3, 15)
        
        if result["rpc_urls"]:
            result["score_components"]["rpc_urls"] = 10
        
        if result["websocket_urls"]:
            result["score_components"]["websocket_urls"] = 10
        
        if result["program_ids"]:
            result["score_components"]["program_ids"] = 15
        
        if result["admin_routes"]:
            result["score_components"]["admin_routes"] = 10
        
        if result["api_keys_found"]:
            result["score_components"]["potential_keys"] = 15
        
        return result
