# Fox Proof Scanner

Proof-first scanner for authorized security testing of modern Web3 products.

## Why this exists

The original scanner is broad and aggressive, but broad scanners can produce noisy findings. This proof scanner is designed for competition-style reporting where every result needs evidence, confidence, impact, and remediation.

## Profiles

```bash
python3 FOX_PROOF_SCANNER.py --target https://example.com --profile web
python3 FOX_PROOF_SCANNER.py --target https://example.com --profile vercel-next
python3 FOX_PROOF_SCANNER.py --target https://example.com --profile solana-dapp
python3 FOX_PROOF_SCANNER.py --target https://example.com --profile defi
python3 FOX_PROOF_SCANNER.py --target https://example.com --profile crash-game
python3 FOX_PROOF_SCANNER.py --target https://example.com --profile giftcard
python3 FOX_PROOF_SCANNER.py --target https://example.com --profile all
```

## What it checks

### Next.js / Vercel

- Source map exposure
- Build and route manifest exposure
- Hidden route names that suggest admin/auth/debug/API surfaces
- HTML fallback rejection to prevent Vercel false positives

### Frontend secrets

Only high-confidence formats are reported:

- Stripe live keys
- AWS access key IDs
- Google API keys
- Valid-looking JWTs with decodable header/payload
- Solana secret key arrays or `Keypair.fromSecretKey` contexts

Random 32-character build hashes are not reported.

### Solana / Web3

- Solana address extraction
- Context classification for treasury, vault, admin, signer, owner, or upgrade authority references
- RPC endpoint discovery with provider-restriction recommendations
- Privy / wallet / Anchor / Solana fingerprints

### Crash-game fairness review

Static/passive checks for references to:

- `serverSeed`
- `nextSeed`
- `serverSeedHash`
- `provablyFair`
- `game:standard:test:getState`

These are reported as review signals unless confirmed by timing evidence. The scanner does not perform destructive actions or privileged event calls.

### Socket.IO surface

- Engine.IO handshake detection
- Reports whether a Socket.IO endpoint exists and whether unauthenticated polling appears open
- Recommends per-event authorization and payload filtering

### Gift-card / promo surfaces

- Detects gift-card, redeem, promo, coupon, voucher, and balance-check business logic surfaces in public code
- Reports candidate endpoints for manual authorized validation
- Does not brute-force card numbers or promo codes

## Output

The scanner writes:

```text
proof_output/<target>_<timestamp>_findings.json
proof_output/<target>_<timestamp>_report.md
```

Each finding includes:

- severity
- confidence
- category
- location
- proof type
- evidence
- impact
- remediation
- request metadata
- response hash

## Competition strategy

Use a higher confidence threshold when submitting to a bounty program:

```bash
python3 FOX_PROOF_SCANNER.py --target https://example.com --profile all --min-confidence 80
```

Submit only findings with strong proof and clear business impact.

## Important safety boundary

This scanner is proof-first and does not include destructive exploitation, wallet draining, credential use, database dumping, brute forcing, or unauthorized privileged actions.
