#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple
from urllib.parse import parse_qs, urlparse

OBJECT_ID_RE = re.compile(r"/(?:users?|accounts?|orgs?|orders?|invoices?|wallets?|projects?|teams?|payments?|transactions?)/([A-Za-z0-9_\-]{2,64})(?:[/?#]|$)", re.I)
QUERY_PARAM_RE = re.compile(r"[?&]([A-Za-z0-9_\-]{2,40})=([^&#]{1,160})")
GRAPHQL_OP_RE = re.compile(r"\b(query|mutation|subscription)\s+([A-Za-z0-9_]+)", re.I)
JSON_KEY_RE = re.compile(r'"([A-Za-z0-9_\-]{2,50})"\s*:')

RISKY_PARAM_MAP = {
    "user": "IDOR/BOLA risk",
    "userid": "IDOR/BOLA risk",
    "user_id": "IDOR/BOLA risk",
    "account": "tenant/account boundary risk",
    "accountid": "tenant/account boundary risk",
    "account_id": "tenant/account boundary risk",
    "org": "tenant isolation risk",
    "orgid": "tenant isolation risk",
    "org_id": "tenant isolation risk",
    "tenant": "tenant isolation risk",
    "tenantid": "tenant isolation risk",
    "role": "privilege trust risk",
    "admin": "privilege trust risk",
    "isadmin": "privilege trust risk",
    "price": "business logic price manipulation risk",
    "amount": "business logic amount manipulation risk",
    "balance": "business logic balance manipulation risk",
    "discount": "coupon/discount abuse risk",
    "coupon": "coupon/discount abuse risk",
    "redirect": "open redirect risk",
    "redirect_uri": "OAuth redirect risk",
    "returnurl": "open redirect risk",
    "next": "open redirect risk",
    "url": "SSRF/open redirect input risk",
    "callback": "callback/SSRF input risk",
    "file": "file disclosure input risk",
    "path": "path traversal input risk",
    "wallet": "Web3 wallet/account manipulation risk",
    "to": "Web3 recipient manipulation risk",
}

BUSINESS_WORDS = {
    "billing": "billing/export/payment surface",
    "invoice": "invoice/payment surface",
    "payment": "payment flow",
    "checkout": "checkout flow",
    "refund": "refund flow",
    "coupon": "discount/coupon flow",
    "price": "price calculation",
    "balance": "balance/accounting logic",
    "role": "role/permission logic",
    "permission": "role/permission logic",
    "export": "data export surface",
    "upload": "file upload surface",
    "transfer": "ownership/funds transfer surface",
    "withdraw": "fund withdrawal surface",
    "deposit": "fund deposit surface",
}

SENSITIVE_RESPONSE_KEYS = {
    "email", "role", "isadmin", "admin", "password", "token", "secret", "apikey", "api_key",
    "phone", "address", "ssn", "creditcard", "card", "balance", "invoice", "billing",
    "wallet", "privatekey", "private_key", "permissions", "session", "refresh_token",
}

WEB3_RISK_WORDS = {
    "signmessage": "signMessage flow",
    "signtransaction": "transaction signing flow",
    "sendtransaction": "transaction sending flow",
    "slippage": "slippage control",
    "programid": "Solana program selection",
    "recipient": "recipient selection",
    "destination": "destination account selection",
    "approve": "token approval flow",
    "delegate": "delegation flow",
}

HIGH_RISK_GRAPHQL = {
    "updateuserrole", "deleteuser", "exportusers", "createadmin", "refundpayment",
    "updatebalance", "transferownership", "setpermissions", "withdraw", "payout",
    "createapiKey", "rotatekey", "impersonateuser",
}


@dataclass
class Gear3Finding:
    type: str
    severity: str
    confidence: int
    title: str
    location: str
    evidence: str
    exploitability: Dict[str, Any]
    attacker_value: str
    safe_next_steps: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class AttackPath:
    title: str
    severity: str
    confidence: int
    steps: List[str]
    impact: str
    proof_refs: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def normalize_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (value or "").lower())


def classify_response(status: int, body: str, content_type: str = "") -> Dict[str, Any]:
    text = body or ""
    low = text.lower()
    keys = sorted(set(k.lower() for k in JSON_KEY_RE.findall(text)))[:200]
    sensitive_keys = sorted(k for k in keys if normalize_key(k) in {normalize_key(x) for x in SENSITIVE_RESPONSE_KEYS})
    labels: List[str] = []
    if status in {401, 403}:
        labels.append("auth_blocked")
    if status == 200:
        labels.append("reachable")
    if "application/json" in (content_type or "").lower() or text.strip().startswith(("{", "[")):
        labels.append("json_like")
    if sensitive_keys:
        labels.append("sensitive_fields")
    if "admin" in low or "permission" in low or "role" in low:
        labels.append("privilege_terms")
    if "invoice" in low or "billing" in low or "payment" in low:
        labels.append("financial_terms")
    if "error" in low and any(x in low for x in ["sql", "prisma", "graphql", "stack", "trace"]):
        labels.append("backend_error")
    if any(x in low for x in ["signtransaction", "signmessage", "window.solana", "isphantom"]):
        labels.append("web3_runtime_terms")
    return {"status": status, "labels": labels, "json_keys": keys[:80], "sensitive_keys": sensitive_keys[:40], "length": len(text)}


def extract_parameter_risks(urls: Iterable[str]) -> List[Gear3Finding]:
    findings: List[Gear3Finding] = []
    seen: Set[str] = set()
    for url in urls:
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        for key, values in params.items():
            nk = normalize_key(key)
            risk = None
            for risky_key, label in RISKY_PARAM_MAP.items():
                if nk == normalize_key(risky_key) or normalize_key(risky_key) in nk:
                    risk = label
                    break
            if not risk:
                continue
            marker = f"{parsed.path}:{key}:{risk}"
            if marker in seen:
                continue
            seen.add(marker)
            findings.append(Gear3Finding(
                type="PARAMETER_TAMPER_RISK",
                severity="MEDIUM" if any(x in risk for x in ["IDOR", "tenant", "privilege", "business"]) else "LOW",
                confidence=68,
                title=f"Risky parameter: {key}",
                location=url,
                evidence=f"Parameter `{key}` maps to {risk}",
                exploitability={"required_access": "depends on endpoint", "safe_mode": "classification only", "blast_radius": "unknown until auth matrix confirms"},
                attacker_value="May indicate IDOR, tenant isolation, privilege, redirect, file, or business-logic attack surface.",
                safe_next_steps=["Compare public vs user access", "Test only safe GET requests", "Verify server-side ownership and role checks"],
            ))
    return findings


def extract_idor_candidates(urls: Iterable[str]) -> List[Gear3Finding]:
    findings: List[Gear3Finding] = []
    seen: Set[str] = set()
    for url in urls:
        match = OBJECT_ID_RE.search(urlparse(url).path + "/")
        if not match:
            continue
        kind = match.group(0).strip("/").split("/")[0]
        object_id = match.group(1)
        key = f"{kind}:{urlparse(url).path}"
        if key in seen:
            continue
        seen.add(key)
        conf = 74 if kind.lower() in {"users", "accounts", "orgs", "orders", "invoices", "wallets"} else 62
        findings.append(Gear3Finding(
            type="IDOR_BOLA_CANDIDATE",
            severity="HIGH" if conf >= 70 else "MEDIUM",
            confidence=conf,
            title=f"Object endpoint candidate: {kind}/{object_id}",
            location=url,
            evidence=f"Object identifier `{object_id}` found in `{kind}` endpoint path.",
            exploitability={"required_access": "normal user token recommended", "safe_method": "GET/HEAD only", "confirmation": "compare owner fields/status/body shape across user contexts"},
            attacker_value="If ownership checks are weak, attackers may access or manipulate another user's/tenant's object data.",
            safe_next_steps=["Run with --headers for user context", "Compare with second user context when available", "Do not mutate objects unless explicitly authorized"],
        ))
    return findings


def extract_business_logic_risks(urls: Iterable[str], blobs: Dict[str, str]) -> List[Gear3Finding]:
    findings: List[Gear3Finding] = []
    seen: Set[str] = set()
    haystacks = list(urls) + list(blobs.keys()) + list(blobs.values())
    for word, label in BUSINESS_WORDS.items():
        hits = []
        for item in haystacks[:400]:
            if word in (item or "").lower():
                hits.append(str(item)[:180])
            if len(hits) >= 5:
                break
        if not hits:
            continue
        if label in seen:
            continue
        seen.add(label)
        severity = "HIGH" if word in {"refund", "billing", "payment", "balance", "withdraw", "transfer"} else "MEDIUM"
        findings.append(Gear3Finding(
            type="BUSINESS_LOGIC_SURFACE",
            severity=severity,
            confidence=70,
            title=f"Business logic surface: {label}",
            location="site/app intelligence",
            evidence=" | ".join(hits[:3]),
            exploitability={"required_access": "usually user", "confirmation": "server-side validation/authorization testing", "mutation_safe_default": "do not perform state-changing requests"},
            attacker_value="Business-logic flaws can enable fraud, unauthorized refunds, billing abuse, export abuse, or account manipulation.",
            safe_next_steps=["Verify server recalculates price/amount", "Verify ownership and role checks", "Review dangerous operations in OpenAPI/GraphQL"],
        ))
    return findings


def extract_graphql_attack_surface(blobs: Dict[str, str]) -> List[Gear3Finding]:
    findings: List[Gear3Finding] = []
    seen: Set[str] = set()
    for location, text in blobs.items():
        for kind, name in GRAPHQL_OP_RE.findall(text or "")[:200]:
            norm = normalize_key(name)
            if norm in seen:
                continue
            seen.add(norm)
            high = norm in {normalize_key(x) for x in HIGH_RISK_GRAPHQL} or any(w in norm for w in ["admin", "role", "delete", "billing", "refund", "balance", "withdraw", "export"])
            findings.append(Gear3Finding(
                type="GRAPHQL_ATTACK_SURFACE",
                severity="HIGH" if high else "MEDIUM",
                confidence=78 if high else 64,
                title=f"GraphQL {kind}: {name}",
                location=location,
                evidence=f"Discovered GraphQL operation `{kind} {name}`",
                exploitability={"required_access": "depends on resolver", "confirmation": "auth matrix on GraphQL endpoint", "safe_probe": "schema/operation classification only"},
                attacker_value="Risky GraphQL operations may expose admin actions, billing operations, exports, or weak resolver authorization.",
                safe_next_steps=["Check resolver-level authorization", "Compare public vs user responses", "Disable verbose GraphQL errors"],
            ))
    return findings


def extract_web3_transaction_risks(blobs: Dict[str, str]) -> List[Gear3Finding]:
    findings: List[Gear3Finding] = []
    combined = "\n".join(blobs.values()).lower()
    if not combined:
        return findings
    hits = []
    for word, label in WEB3_RISK_WORDS.items():
        if word in combined:
            hits.append(label)
    if hits:
        severity = "HIGH" if any("transaction" in h or "recipient" in h or "approval" in h for h in hits) else "MEDIUM"
        findings.append(Gear3Finding(
            type="WEB3_TRANSACTION_RISK_SURFACE",
            severity=severity,
            confidence=76,
            title="Web3 transaction/signature risk surface",
            location="frontend JavaScript",
            evidence=", ".join(sorted(set(hits))),
            exploitability={"required_access": "wallet interaction", "confirmation": "review transaction construction and wallet prompt", "safe_mode": "static/runtime classification only"},
            attacker_value="Unsafe signing/transaction construction can create wallet-loss, misleading prompt, slippage, or recipient-manipulation risk.",
            safe_next_steps=["Verify nonce/domain binding for signMessage", "Verify recipient/program IDs are trusted", "Verify slippage and amount controls server/app-side"],
        ))
    if "signmessage" in combined and not any(x in combined for x in ["nonce", "domain", "origin", "statement"]):
        findings.append(Gear3Finding(
            type="WEB3_SIGNMESSAGE_CONTEXT_RISK",
            severity="MEDIUM",
            confidence=68,
            title="signMessage context binding not obvious",
            location="frontend JavaScript",
            evidence="signMessage appears without obvious nonce/domain/origin markers nearby in collected JS.",
            exploitability={"required_access": "wallet interaction", "confirmation": "manual code review", "risk": "replay or misleading signature flow if server binding is absent"},
            attacker_value="Weak signature context may support replay, phishing-style approvals, or account-linking abuse.",
            safe_next_steps=["Check server verifies nonce/domain/origin", "Check message text shown to user", "Check expiration/replay protection"],
        ))
    return findings


def build_attack_paths(findings: List[Gear3Finding], base_findings: Optional[List[Dict[str, Any]]] = None, access_matrix: Optional[List[Dict[str, Any]]] = None) -> List[AttackPath]:
    paths: List[AttackPath] = []
    base_findings = base_findings or []
    access_matrix = access_matrix or []
    exposed_admin = [f for f in base_findings if f.get("type") in {"BROKEN_ADMIN_ACCESS_CONTROL", "PUBLIC_ADMIN_ENDPOINT"}]
    data_exposure = [f for f in base_findings if "SECRET" in f.get("type", "") or "CONFIG" in f.get("type", "") or "KEY" in f.get("type", "")]
    idor = [f for f in findings if f.type == "IDOR_BOLA_CANDIDATE"]
    params = [f for f in findings if f.type == "PARAMETER_TAMPER_RISK"]
    gql = [f for f in findings if f.type == "GRAPHQL_ATTACK_SURFACE" and f.severity == "HIGH"]
    biz = [f for f in findings if f.type == "BUSINESS_LOGIC_SURFACE" and f.severity == "HIGH"]
    web3 = [f for f in findings if f.type.startswith("WEB3_")]

    if exposed_admin:
        first = exposed_admin[0]
        paths.append(AttackPath(
            title="Admin access-control proof path",
            severity="CRITICAL" if first.get("severity") == "CRITICAL" else "HIGH",
            confidence=int(first.get("confidence", 88)),
            steps=["Admin/internal route discovered", f"Proof: {first.get('evidence', '')}", "Impact modeled as admin data/action exposure"],
            impact="Possible admin-level data access, fraud, account takeover, or internal data exposure.",
            proof_refs=[first.get("location", "")],
        ))
    if data_exposure:
        first = data_exposure[0]
        paths.append(AttackPath(
            title="Sensitive backend exposure path",
            severity=first.get("severity", "HIGH"),
            confidence=int(first.get("confidence", 85)),
            steps=["Sensitive config/secret-like material detected", f"Location: {first.get('location', '')}", "Evidence was redacted for safe proof"],
            impact="Possible API abuse, cloud abuse, payment abuse, token forgery, or database access depending on key scope.",
            proof_refs=[first.get("location", "")],
        ))
    if idor and params:
        paths.append(AttackPath(
            title="Object access-control candidate path",
            severity="HIGH",
            confidence=min(88, max(idor[0].confidence, params[0].confidence) + 8),
            steps=["Object endpoint discovered", idor[0].evidence, "Risky user/account/org parameter found", params[0].evidence, "Auth differential can confirm BOLA/IDOR"],
            impact="Possible cross-user or cross-tenant data exposure if server-side ownership checks are weak.",
            proof_refs=[idor[0].location, params[0].location],
        ))
    if gql:
        paths.append(AttackPath(
            title="GraphQL high-risk operation path",
            severity="HIGH",
            confidence=gql[0].confidence,
            steps=["GraphQL operation discovered", gql[0].evidence, "Operation name suggests admin/billing/delete/export behavior", "Auth matrix should verify resolver protection"],
            impact="Possible weak resolver authorization, sensitive export, billing abuse, or account manipulation.",
            proof_refs=[gql[0].location],
        ))
    if biz:
        paths.append(AttackPath(
            title="Business logic abuse review path",
            severity="HIGH",
            confidence=biz[0].confidence,
            steps=["High-value business endpoint/logic discovered", biz[0].evidence, "Requires server-side validation and authorization review"],
            impact="Possible fraud, refund abuse, billing abuse, export abuse, or balance manipulation if controls are weak.",
            proof_refs=[biz[0].location],
        ))
    if web3:
        paths.append(AttackPath(
            title="Web3 transaction/signature review path",
            severity=web3[0].severity,
            confidence=web3[0].confidence,
            steps=["Web3 transaction/signature logic discovered", web3[0].evidence, "Review wallet prompts, nonce/domain binding, recipient/program selection, slippage/amount controls"],
            impact="Potential wallet/signature abuse risk if frontend transaction construction is unsafe.",
            proof_refs=[web3[0].location],
        ))
    return sorted(paths, key=lambda p: (p.confidence, severity_score(p.severity)), reverse=True)


def severity_score(severity: str) -> int:
    return {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}.get((severity or "").upper(), 0)


def build_gear3_report(site_map: Dict[str, Any], findings: Optional[List[Dict[str, Any]]] = None, access_matrix: Optional[List[Dict[str, Any]]] = None, blobs: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    findings = findings or []
    access_matrix = access_matrix or []
    blobs = blobs or {}
    urls = sorted(set((site_map.get("endpoints") or []) + (site_map.get("admin_candidates") or []) + (site_map.get("graphql_candidates") or []) + list(blobs.keys())))
    gear_findings: List[Gear3Finding] = []
    gear_findings.extend(extract_parameter_risks(urls))
    gear_findings.extend(extract_idor_candidates(urls))
    gear_findings.extend(extract_business_logic_risks(urls, blobs))
    gear_findings.extend(extract_graphql_attack_surface(blobs))
    gear_findings.extend(extract_web3_transaction_risks(blobs))

    response_classes = []
    for row in access_matrix[:120]:
        labels = []
        for ctx in ["public", "user", "admin"]:
            if ctx in row:
                if row[ctx] in {401, 403}:
                    labels.append(f"{ctx}:blocked")
                elif row[ctx] == 200:
                    labels.append(f"{ctx}:reachable")
        if labels:
            response_classes.append({"url": row.get("url"), "labels": labels, "statuses": row})

    attack_paths = build_attack_paths(gear_findings, findings, access_matrix)
    return {
        "summary": {
            "total_gear3_findings": len(gear_findings),
            "attack_paths": len(attack_paths),
            "high_or_critical": sum(1 for f in gear_findings if f.severity in {"HIGH", "CRITICAL"}),
            "response_classes": len(response_classes),
        },
        "findings": [f.to_dict() for f in sorted(gear_findings, key=lambda x: (x.confidence, severity_score(x.severity)), reverse=True)],
        "attack_paths": [p.to_dict() for p in attack_paths],
        "response_classification": response_classes,
    }
