#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, Iterable, List, Optional, Set
from urllib.parse import urlparse

SECRET_PATTERNS = [
    ("AWS_ACCESS_KEY_ID", re.compile(r"\bAKIA[0-9A-Z]{16}\b"), 92, "cloud/API abuse risk"),
    ("AWS_TEMP_ACCESS_KEY", re.compile(r"\bASIA[0-9A-Z]{16}\b"), 90, "temporary cloud credential risk"),
    ("STRIPE_SECRET_KEY", re.compile(r"\bsk_(?:live|test)_[A-Za-z0-9]{16,}\b"), 94, "payment API abuse risk"),
    ("SUPABASE_SERVICE_ROLE", re.compile(r"(?i)\bSUPABASE_SERVICE_ROLE_KEY\b\s*[:=]\s*[\"']?[^\s\"']{20,}"), 94, "database bypass/backend API abuse risk"),
    ("FIREBASE_PRIVATE_KEY", re.compile(r"(?i)\bFIREBASE_PRIVATE_KEY\b\s*[:=]\s*[\"']?[^\n\r]{20,}"), 95, "service-account signing risk"),
    ("GOOGLE_API_KEY", re.compile(r"\bAIza[0-9A-Za-z_\-]{35}\b"), 78, "Google API quota or data access risk"),
    ("GITHUB_TOKEN", re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9_]{20,}\b"), 92, "source/code or CI access risk"),
    ("OPENAI_API_KEY", re.compile(r"\bsk-[A-Za-z0-9]{20,}\b"), 88, "paid API abuse risk"),
    ("SENDGRID_KEY", re.compile(r"\bSG\.[A-Za-z0-9_\-]{16,}\.[A-Za-z0-9_\-]{16,}\b"), 91, "email abuse/phishing infrastructure risk"),
    ("PRIVATE_KEY_BLOCK", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |)?PRIVATE KEY-----"), 98, "signing/decryption credential exposure risk"),
    ("JWT", re.compile(r"\beyJ[A-Za-z0-9_\-]{8,}\.[A-Za-z0-9_\-]{8,}\.[A-Za-z0-9_\-]{8,}\b"), 72, "session or authorization token exposure risk"),
    ("DATABASE_URL", re.compile(r"(?i)\b(?:postgres|postgresql|mysql|mongodb|redis)://[^\s\"'<>]{12,}"), 95, "database access risk"),
    ("JWT_SECRET", re.compile(r"(?i)\bJWT_SECRET\b\s*[:=]\s*[\"']?[^\s\"']{12,}"), 94, "token forgery risk"),
    ("GENERIC_BACKEND_SECRET", re.compile(r"(?i)\b(?:API_KEY|SECRET_KEY|CLIENT_SECRET|ACCESS_TOKEN|PRIVATE_KEY|SERVICE_ROLE)\b\s*[:=]\s*[\"']?[A-Za-z0-9_./+\-]{16,}"), 74, "backend secret-like exposure risk"),
]

DATA_PATTERNS = [
    ("EMAIL_ADDRESS", re.compile(r"\b[A-Za-z0-9._%+\-]{2,}@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b"), 55),
    ("PHONE_NUMBER", re.compile(r"(?<!\d)(?:\+?\d[\d .()\-]{8,}\d)(?!\d)"), 45),
    ("INTERNAL_IP", re.compile(r"\b(?:10\.|172\.(?:1[6-9]|2\d|3[01])\.|192\.168\.)\d{1,3}\.\d{1,3}\b"), 62),
    ("SOLANA_WALLET", re.compile(r"\b[1-9A-HJ-NP-Za-km-z]{32,44}\b"), 42),
]

STORAGE_PATTERNS = [
    ("AWS_S3", re.compile(r"https?://[a-z0-9.\-]+\.s3(?:[.\-][a-z0-9\-]+)?\.amazonaws\.com[^\s\"'<>]*", re.I)),
    ("AWS_S3_WEBSITE", re.compile(r"https?://[a-z0-9.\-]+\.s3-website[.\-][a-z0-9\-]+\.amazonaws\.com[^\s\"'<>]*", re.I)),
    ("GCS", re.compile(r"https?://storage\.googleapis\.com/[A-Za-z0-9._\-/]+", re.I)),
    ("AZURE_BLOB", re.compile(r"https?://[a-z0-9\-]+\.blob\.core\.windows\.net/[A-Za-z0-9._\-/]+", re.I)),
    ("CLOUDFLARE_R2", re.compile(r"https?://[A-Za-z0-9\-.]+\.r2\.cloudflarestorage\.com[^\s\"'<>]*", re.I)),
    ("SUPABASE_STORAGE", re.compile(r"https?://[a-z0-9\-]+\.supabase\.co/storage/v1/object/[^\s\"'<>]+", re.I)),
    ("IPFS", re.compile(r"https?://[^\s\"'<>]*(?:ipfs|gateway)[^\s\"'<>]*/ipfs/[A-Za-z0-9]+", re.I)),
    ("ARWEAVE", re.compile(r"https?://arweave\.net/[A-Za-z0-9_\-]+", re.I)),
]

ERROR_SIGNATURES = [
    ("LARAVEL_DEBUG", re.compile(r"Whoops!|Laravel|APP_DEBUG|Illuminate\\\\", re.I)),
    ("DJANGO_DEBUG", re.compile(r"Django|Traceback|Exception Type|Request Method", re.I)),
    ("EXPRESS_STACK", re.compile(r"Express|at Layer\.handle|node_modules", re.I)),
    ("NEXTJS_ERROR", re.compile(r"__NEXT_DATA__|Next\.js|next/dist/server", re.I)),
    ("PRISMA_ERROR", re.compile(r"PrismaClient(?:KnownRequest)?Error|prisma\.", re.I)),
    ("POSTGRES_ERROR", re.compile(r"PostgreSQL|PG::|psql:|SQLSTATE|syntax error at or near", re.I)),
    ("MYSQL_ERROR", re.compile(r"MySQL|MariaDB|SQL syntax.*MySQL|Warning: mysql_", re.I)),
    ("MONGO_ERROR", re.compile(r"MongoError|MongooseError|MongoServerError", re.I)),
    ("GRAPHQL_ERROR", re.compile(r"GraphQLError|Cannot query field|Cannot return null for non-nullable field", re.I)),
]

SENSITIVE_FILENAMES = re.compile(r"(?i)(backup|dump|users|export|database|db|\.env|secret|private|credential|wallet|key).{0,40}\.(?:sql|csv|json|env|bak|zip|gz|tar|pem|key)")
SOURCE_MAP_HINT = re.compile(r"sourceMappingURL=([^\s*]+\.map)|\"sources\"\s*:\s*\[|\"webpack://", re.I)
OPENAPI_HINT = re.compile(r"\b(?:openapi|swagger)\b|\"paths\"\s*:\s*\{|\"components\"\s*:\s*\{", re.I)
GRAPHQL_HINT = re.compile(r"\b(query|mutation)\s+[A-Za-z0-9_]+|/graphql\b|GraphQLError", re.I)


@dataclass
class ExposureFinding:
    type: str
    category: str
    severity: str
    confidence: int
    location: str
    evidence: str
    attacker_value: str
    remediation: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def redact_secret(text: str, unfiltered: bool = False) -> str:
    """
    Redact secrets from text for safe output.
    
    Args:
        text: Text to redact
        unfiltered: If True, return raw text without redaction (for authorized judge review)
    """
    value = str(text or "")
    if unfiltered:
        return value  # Return full unredacted text for judge mode
    for name, pattern, _, _ in SECRET_PATTERNS:
        value = pattern.sub(lambda m: _mask_match(m.group(0), name), value)
    value = re.sub(r"(?i)(password|secret|token|api[_-]?key|private[_-]?key)(\s*[:=]\s*)([^\s\"']{8,})", r"\1\2<redacted>", value)
    return value[:700]


def _mask_match(value: str, label: str) -> str:
    if "PRIVATE KEY" in value:
        return f"-----BEGIN <redacted {label}>-----"
    if len(value) <= 12:
        return f"<{label}:redacted>"
    return f"{value[:6]}...<{label}:redacted>...{value[-4:]}"


def classify_secret(name: str, confidence: int) -> str:
    if confidence >= 95:
        return "CRITICAL"
    if confidence >= 88:
        return "HIGH"
    if confidence >= 70:
        return "MEDIUM"
    return "LOW"


def sample_lines(text: str, pattern: re.Pattern, max_lines: int = 3, unfiltered: bool = False) -> List[str]:
    out: List[str] = []
    for line in (text or "").splitlines():
        if pattern.search(line):
            out.append(redact_secret(line.strip(), unfiltered=unfiltered))
        if len(out) >= max_lines:
            break
    return out


def scan_text_for_exposures(location: str, text: str, content_type: str = "", unfiltered: bool = False) -> List[ExposureFinding]:
    findings: List[ExposureFinding] = []
    seen: Set[str] = set()
    body = text or ""
    for name, pattern, confidence, value in SECRET_PATTERNS:
        matches = list(pattern.finditer(body))[:5]
        if not matches:
            continue
        key = f"secret:{name}:{location}"
        if key in seen:
            continue
        seen.add(key)
        evidence = "; ".join(redact_secret(m.group(0), unfiltered=unfiltered) for m in matches[:3])
        findings.append(ExposureFinding(
            type=name,
            category="secret_exposure",
            severity=classify_secret(name, confidence),
            confidence=confidence,
            location=location,
            evidence=evidence,
            attacker_value=value,
            remediation="Rotate the exposed value, move privileged credentials server-side, and restrict key scope/allowed origins.",
            metadata={"matches": len(matches), "content_type": content_type},
        ))
    for name, pattern, base_conf in DATA_PATTERNS:
        matches = list(pattern.finditer(body))[:50]
        if len(matches) < (3 if name in {"EMAIL_ADDRESS", "PHONE_NUMBER"} else 1):
            continue
        samples = [redact_pii(m.group(0), name) for m in matches[:5]]
        findings.append(ExposureFinding(
            type=name,
            category="data_leak_signal",
            severity="LOW" if base_conf < 60 else "MEDIUM",
            confidence=min(85, base_conf + min(len(matches), 20)),
            location=location,
            evidence=f"{len(matches)} occurrence(s), samples: {', '.join(samples)}",
            attacker_value="May support phishing, fraud, user targeting, or internal recon when combined with other data.",
            remediation="Avoid exposing unnecessary personal/internal data; minimize returned fields and require authorization.",
            metadata={"sample_count": len(samples)},
        ))
    for name, pattern in STORAGE_PATTERNS:
        urls = sorted(set(m.group(0).rstrip(".,);]") for m in pattern.finditer(body)))[:10]
        if not urls:
            continue
        suspicious = [u for u in urls if SENSITIVE_FILENAMES.search(u)]
        conf = 82 if suspicious else 65
        findings.append(ExposureFinding(
            type=name,
            category="storage_reference",
            severity="HIGH" if suspicious else "MEDIUM",
            confidence=conf,
            location=location,
            evidence="; ".join(redact_secret(u, unfiltered=unfiltered) for u in urls[:5]),
            attacker_value="Public storage references may expose backups, exports, uploads, or sensitive assets if permissions are weak.",
            remediation="Review bucket/object ACLs, disable public listing, and remove sensitive files from public storage.",
            metadata={"urls": urls[:10], "sensitive_filename_hits": suspicious[:5]},
        ))
    for name, pattern in ERROR_SIGNATURES:
        if pattern.search(body):
            findings.append(ExposureFinding(
                type=name,
                category="backend_error_intel",
                severity="MEDIUM",
                confidence=78,
                location=location,
                evidence="; ".join(sample_lines(body, pattern, 2, unfiltered=unfiltered)) or name,
                attacker_value="Verbose errors reveal backend stack, file paths, schemas, or framework behavior useful for targeted exploitation.",
                remediation="Disable debug mode, return generic errors to users, and log detailed traces server-side only.",
                metadata={"content_type": content_type},
            ))
    if SOURCE_MAP_HINT.search(body):
        findings.append(ExposureFinding(
            type="SOURCE_MAP_EXPOSURE_SIGNAL",
            category="source_map_intel",
            severity="MEDIUM",
            confidence=72,
            location=location,
            evidence="Source map or original source metadata marker detected.",
            attacker_value="Source maps can reveal original source files, comments, hidden routes, and secret-like strings.",
            remediation="Do not publish production source maps unless access-controlled; strip comments/secrets from bundles.",
        ))
    if OPENAPI_HINT.search(body):
        findings.append(ExposureFinding(
            type="OPENAPI_SCHEMA_SIGNAL",
            category="api_schema_intel",
            severity="MEDIUM",
            confidence=70,
            location=location,
            evidence="OpenAPI/Swagger schema markers detected.",
            attacker_value="Public API schemas speed up endpoint enumeration and authorization testing.",
            remediation="Review public schemas and remove internal/admin operations from unauthenticated docs.",
        ))
    if GRAPHQL_HINT.search(body):
        findings.append(ExposureFinding(
            type="GRAPHQL_SCHEMA_OR_QUERY_SIGNAL",
            category="graphql_intel",
            severity="MEDIUM",
            confidence=68,
            location=location,
            evidence="GraphQL endpoint/query/error markers detected.",
            attacker_value="GraphQL metadata can reveal objects, mutations, and resolver authorization surfaces.",
            remediation="Enforce resolver authorization and avoid verbose GraphQL errors in production.",
        ))
    return dedupe_findings(findings)


def redact_pii(value: str, kind: str) -> str:
    if kind == "EMAIL_ADDRESS" and "@" in value:
        user, domain = value.split("@", 1)
        return f"{user[:1]}***@{domain}"
    if kind == "PHONE_NUMBER":
        digits = re.sub(r"\D", "", value)
        return f"***{digits[-4:]}" if len(digits) >= 4 else "<redacted-phone>"
    if kind == "SOLANA_WALLET":
        return value[:4] + "..." + value[-4:]
    return value


def dedupe_findings(findings: Iterable[ExposureFinding]) -> List[ExposureFinding]:
    seen: Set[str] = set()
    out: List[ExposureFinding] = []
    for f in findings:
        key = f"{f.type}:{f.location}:{f.evidence[:80]}"
        if key in seen:
            continue
        seen.add(key)
        out.append(f)
    return sorted(out, key=lambda x: (x.confidence, severity_score(x.severity)), reverse=True)


def severity_score(sev: str) -> int:
    return {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}.get((sev or "").upper(), 0)


def extract_openapi_summary(location: str, text: str) -> Dict[str, Any]:
    try:
        data = json.loads(text)
    except Exception:
        return {"location": location, "valid_json": False, "paths": [], "admin_paths": [], "dangerous_ops": []}
    paths = sorted((data.get("paths") or {}).keys()) if isinstance(data, dict) else []
    admin_paths = [p for p in paths if any(w in p.lower() for w in ["admin", "internal", "billing", "role", "user", "token"])]
    dangerous_ops: List[str] = []
    for path, methods in (data.get("paths") or {}).items():
        if not isinstance(methods, dict):
            continue
        for method, spec in methods.items():
            combo = f"{method.upper()} {path}"
            blob = json.dumps(spec).lower() if isinstance(spec, dict) else ""
            if any(w in combo.lower() + blob for w in ["delete", "admin", "role", "billing", "payment", "upload", "export", "token"]):
                dangerous_ops.append(combo)
    return {"location": location, "valid_json": True, "paths": paths[:300], "admin_paths": admin_paths[:100], "dangerous_ops": dangerous_ops[:100]}


def extract_source_map_summary(location: str, text: str) -> Dict[str, Any]:
    try:
        data = json.loads(text)
    except Exception:
        return {"location": location, "valid_json": False, "sources": [], "interesting_sources": [], "comments": []}
    sources = data.get("sources") if isinstance(data, dict) else []
    if not isinstance(sources, list):
        sources = []
    interesting = [s for s in sources if any(w in str(s).lower() for w in ["admin", "auth", "secret", "token", "wallet", "billing", "server", "api"])]
    source_content = data.get("sourcesContent") if isinstance(data, dict) else []
    comments: List[str] = []
    if isinstance(source_content, list):
        for content in source_content[:50]:
            for line in str(content).splitlines():
                if re.search(r"(?i)TODO|FIXME|SECURITY|HACK|auth|admin|secret", line):
                    comments.append(redact_secret(line.strip()))
                    if len(comments) >= 20:
                        break
            if len(comments) >= 20:
                break
    return {"location": location, "valid_json": True, "sources": [str(s) for s in sources[:300]], "interesting_sources": [str(s) for s in interesting[:100]], "comments": comments}


def extract_graphql_summary(location: str, text: str) -> Dict[str, Any]:
    operations = sorted(set(re.findall(r"\b(query|mutation|subscription)\s+([A-Za-z0-9_]+)", text or "", re.I)))
    fields = sorted(set(re.findall(r"\b(admin[A-Za-z0-9_]*|update[A-Za-z0-9_]*|delete[A-Za-z0-9_]*|create[A-Za-z0-9_]*|billing[A-Za-z0-9_]*|user[A-Za-z0-9_]*)\b", text or "", re.I)))[:100]
    return {"location": location, "operations": [f"{kind} {name}" for kind, name in operations[:100]], "interesting_fields": fields}


def build_data_exposure_report(blobs: Dict[str, str], content_types: Optional[Dict[str, str]] = None, unfiltered: bool = False) -> Dict[str, Any]:
    content_types = content_types or {}
    findings: List[ExposureFinding] = []
    openapi: List[Dict[str, Any]] = []
    sourcemaps: List[Dict[str, Any]] = []
    graphql: List[Dict[str, Any]] = []
    for location, text in blobs.items():
        ctype = content_types.get(location, "")
        findings.extend(scan_text_for_exposures(location, text, ctype, unfiltered=unfiltered))
        if OPENAPI_HINT.search(text or "") or location.endswith(("swagger.json", "openapi.json")):
            openapi.append(extract_openapi_summary(location, text))
        if SOURCE_MAP_HINT.search(text or "") or location.endswith(".map"):
            sourcemaps.append(extract_source_map_summary(location, text))
        if GRAPHQL_HINT.search(text or "") or "graphql" in location.lower():
            graphql.append(extract_graphql_summary(location, text))
    findings = dedupe_findings(findings)
    return {
        "summary": {
            "total_findings": len(findings),
            "critical_or_high": sum(1 for f in findings if f.severity in {"CRITICAL", "HIGH"}),
            "categories": category_counts(findings),
        },
        "findings": [f.to_dict() for f in findings],
        "openapi": openapi,
        "source_maps": sourcemaps,
        "graphql": graphql,
    }


def category_counts(findings: Iterable[ExposureFinding]) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for f in findings:
        counts[f.category] = counts.get(f.category, 0) + 1
    return counts
