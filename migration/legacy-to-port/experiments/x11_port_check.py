"""Check the PORT's sas_best(x, 32) against the SAS log of X11 (and the BEST32. lines of X09).
Usage (repo root): uv run --project port python migration/legacy-to-port/experiments/x11_port_check.py"""

import re
import struct
from pathlib import Path

from credit_risk import sas_compat

HERE = Path(__file__).parent
rows = [(m.group(1), m.group(2).strip()) for m in re.finditer(r"^X11 ([0-9A-F]{16}) \[(.*)\]$", (HERE / "x11_best32.log").read_text(), re.M)]
rows += re.findall(r"^X09 best32 x=([0-9A-F]{16}) x=(\S+)$", (HERE / "x09_input_numeric.log").read_text(), re.M)
bad = [(h, t, p) for h, t in rows if (p := sas_compat.sas_best(struct.unpack(">d", bytes.fromhex(h))[0], 32)) != t]
print(f"X11 + X09: port sas_best(x, 32) equals SAS BEST32. on {len(rows) - len(bad)}/{len(rows)} values")
for h, t, p in bad[:20]:
    print("  ", h, struct.unpack(">d", bytes.fromhex(h))[0], "SAS", t, "port", p)
