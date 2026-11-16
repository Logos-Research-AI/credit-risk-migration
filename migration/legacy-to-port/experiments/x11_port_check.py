"""Check the PORT's sas_best(x, 32) against the SAS logs of X11, X13, X14 and X15 (and the BEST32. lines
of X09). The values that differ are listed: they are all E-notation values of X14, next to a step of
the 14-digit mantissa (see sas_compat._best32).
Usage (repo root): uv run --project port python migration/legacy-to-port/experiments/x11_port_check.py"""

import re
import struct
from pathlib import Path

from credit_risk import sas_compat

HERE = Path(__file__).parent
rows: list[tuple[str, str]] = []
for stem, tag in (("x11_best32", "X11"), ("x13_best32_edges", "X13"), ("x14_best32_enotation", "X14"), ("x15_best32_whole", "X15")):
    rows += [(m.group(1), m.group(2).strip()) for m in re.finditer(rf"^{tag} ([0-9A-F]{{16}}) \[(.*)\]$", (HERE / f"{stem}.log").read_text(), re.M)]
rows = list(dict.fromkeys(rows))
rows += re.findall(r"^X09 best32 x=([0-9A-F]{16}) x=(\S+)$", (HERE / "x09_input_numeric.log").read_text(), re.M)
bad = [(h, t, p) for h, t in rows if (p := sas_compat.sas_best(struct.unpack(">d", bytes.fromhex(h))[0], 32)) != t]
print(f"X11, X13, X14, X15 + X09: port sas_best(x, 32) equals SAS BEST32. on {len(rows) - len(bad)}/{len(rows)} values")
for h, t, p in bad:
    print("  ", h, struct.unpack(">d", bytes.fromhex(h))[0], "SAS", t, "port", p)
