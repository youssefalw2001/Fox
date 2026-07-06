#!/usr/bin/env python3
"""
💀🔥 RISK RANKER - FOX'S SCORING ENGINE 🔥💀

Scores Web3 sites based on public attack surface indicators.
No exploitation claims - just "interesting for authorized followup".
"""

from typing import Dict, List

class RiskRanker:
    """Ranks sites by attack surface score"""
    
    def __init__(self):
        self.scoring_rules = {
            # Web3 indicators (highest value)
            "solana_wallet": 25,
            "privy": 20,
            "phantom": 10,
            "anchor": 15,
            "crash_game": 10,
            "program_ids": 15,
            
            # Framework indicators
            "nextjs": 20,
            "vercel": 20,
            "react": 10,
            "socketio": 15,
            "websocket": 10,
            
            # Intelligence indicators
            "sourcemaps": 15,
            "api_urls": 15,
            "rpc_urls": 10,
            "websocket_urls": 10,
            "admin_routes": 10,
            "potential_keys": 15,
            "many_js_files": 5,
            
            # Infrastructure
            "cloudflare": 5,
            "graphql": 5,
        }
    
    def calculate_score(self, fingerprint_data: Dict, js_analysis: Dict) -> Dict:
        """Calculate risk score for a site"""
        score = 0
        score_breakdown = {}
        detected_features = []
        
        # Score from fingerprinting
        if "score_components" in fingerprint_data:
            for component, component_score in fingerprint_data["score_components"].items():
                score += component_score
                score_breakdown[component] = component_score
                
                # Build detected features list
                if component == "solana_wallet":
                    detected_features.append("Solana wallet adapter")
                elif component == "privy":
                    detected_features.append("Privy")
                elif component == "nextjs":
                    detected_features.append("Next.js")
                elif component == "vercel":
                    detected_features.append("Vercel")
                elif component == "socketio":
                    detected_features.append("Socket.IO")
                elif component == "sourcemaps":
                    detected_features.append("Source maps")
                elif component == "crash_game":
                    detected_features.append("Crash game indicators")
                elif component == "admin_routes":
                    detected_features.append("Admin/debug routes")
        
        # Score from JS analysis
        if "score_components" in js_analysis:
            for component, component_score in js_analysis["score_components"].items():
                score += component_score
                score_breakdown[component] = component_score
                
                if component == "api_urls" and js_analysis.get("api_urls"):
                    detected_features.append(f"API URLs ({len(js_analysis['api_urls'])})")
                elif component == "rpc_urls" and js_analysis.get("rpc_urls"):
                    detected_features.append("RPC URLs")
                elif component == "program_ids" and js_analysis.get("program_ids"):
                    detected_features.append(f"Solana Program IDs ({len(js_analysis['program_ids'])})")
                elif component == "admin_routes" and js_analysis.get("admin_routes"):
                    detected_features.append("Hidden admin routes")
                elif component == "potential_keys" and js_analysis.get("api_keys_found"):
                    detected_features.append("Potential API keys")
        
        # Add JS file count
        js_files_count = len(fingerprint_data.get("js_files", []))
        
        # Classify based on score
        if score >= 80:
            classification = "high_priority_for_authorized_followup"
        elif score >= 60:
            classification = "interesting_for_authorized_followup"
        elif score >= 40:
            classification = "moderate_interest"
        else:
            classification = "low_priority"
        
        return {
            "score": score,
            "score_breakdown": score_breakdown,
            "classification": classification,
            "detected_features": detected_features,
            "js_files_analyzed": js_analysis.get("analyzed_files", 0),
            "js_files_found": js_files_count
        }
    
    def rank_sites(self, sites_data: List[Dict]) -> List[Dict]:
        """Rank all sites by score"""
        ranked = sorted(sites_data, key=lambda x: x.get("score", 0), reverse=True)
        return ranked
    
    def get_top_n(self, ranked_sites: List[Dict], n: int = 3) -> List[Dict]:
        """Get top N sites"""
        return ranked_sites[:n]
