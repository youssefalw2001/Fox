#!/usr/bin/env python3
from __future__ import annotations

from typing import Dict, List

KNOWN_PROGRAMS = {
    "11111111111111111111111111111111": "System Program",
    "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA": "SPL Token Program",
    "ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL": "Associated Token Account Program",
    "ComputeBudget111111111111111111111111111111": "Compute Budget Program",
    "BPFLoaderUpgradeab1e11111111111111111111111": "BPF Upgradeable Loader",
    "675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8": "Raydium AMM v4",
    "JUP6LkbZbjS1jKKwapdHNy74zcZ3tLUZoi5QNyVTaV4": "Jupiter Aggregator v6",
    "whirLbMiicVdio4qvUfM5KAg6Ct8VwpYzGff3uctyCc": "Orca Whirlpool",
    "So11111111111111111111111111111111111111112": "Wrapped SOL Mint",
}

HIGH_VALUE_HINTS = {
    "Raydium AMM v4": "swap/liquidity route",
    "Jupiter Aggregator v6": "aggregated swap route",
    "Orca Whirlpool": "concentrated liquidity route",
    "BPF Upgradeable Loader": "upgrade authority surface",
    "SPL Token Program": "token approval/transfer surface",
}


def label_program_id(program_id: str) -> Dict[str, str]:
    label = KNOWN_PROGRAMS.get(program_id, "Unknown Solana address/program candidate")
    return {
        "program_id": program_id,
        "label": label,
        "hint": HIGH_VALUE_HINTS.get(label, "review context before treating as program logic"),
        "known": str(program_id in KNOWN_PROGRAMS).lower(),
    }


def enrich_solana_intel(site_data: Dict) -> Dict:
    program_ids = site_data.get("js_analysis", {}).get("program_ids", []) or []
    labels: List[Dict[str, str]] = [label_program_id(pid) for pid in sorted(set(program_ids))]
    site_data["solana_intel"] = {
        "total_candidates": len(program_ids),
        "known_programs": [item for item in labels if item["known"] == "true"],
        "unknown_candidates": [item for item in labels if item["known"] != "true"][:100],
    }
    return site_data
