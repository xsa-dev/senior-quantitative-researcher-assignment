#!/usr/bin/env python3
from __future__ import annotations
import subprocess
import sys

PY = sys.executable
cmds = [
    [PY, "scripts/00_discover_data.py"],
    [PY, "scripts/01_parse_pcap.py"],
    [PY, "scripts/02_build_wdo_calendar_spread.py"],
    [PY, "scripts/03_compute_vol_momentum.py"],
    [PY, "scripts/04_gold_arbitrage_research.py"],
    [PY, "-m", "quant_assignment.validation"],
    [PY, "-m", "pytest", "-q"],
]
for c in cmds:
    print("RUN", " ".join(c))
    r = subprocess.run(c)
    if r.returncode != 0:
        sys.exit(r.returncode)
