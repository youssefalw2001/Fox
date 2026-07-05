#!/usr/bin/env python3
"""
💀 SCAN THE REAL BACKEND - backend.rugs.fun 💀
This is where the money actually is
"""

import subprocess
import sys

print("💀🔥 SCANNING THE REAL BACKEND WHERE THE MONEY IS 🔥💀")
print()
print("Target: backend.rugs.fun")
print("This is the ACTUAL API server, not the React frontend")
print()

# Run ULTIMATE_MEGA_SCANNER on the REAL backend
cmd = [
    "python3", "ULTIMATE_MEGA_SCANNER.py",
    "--target", "https://backend.rugs.fun",
    "--full",
    "--exploit",
    "--threads", "20",
    "--timeout", "30",
    "--output", "output/REAL_BACKEND_RUGS_FUN"
]

print(f"🚀 Running: {' '.join(cmd)}")
print()

subprocess.run(cmd)
