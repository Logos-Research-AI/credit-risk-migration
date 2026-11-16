"""Check the PORT's roc_association against the SAS logs of X07, X10, X10b and X12, every column: the
numbers, and the cells as printed (sas_d8), where 0 and 6.11E-78 differ though the numbers hardly do.
Usage (repo root): uv run --project port python migration/legacy-to-port/experiments/x10_port_check.py"""

import json
import re
import struct
from pathlib import Path

import polars as pl

from credit_risk import sas_compat

HERE = Path(__file__).parent
COLS = {"Area": "area", "StdErr": "std_err", "LowerArea": "lower", "UpperArea": "upper", "SomersD": "somers_d", "Gamma": "gamma", "TauA": "tau_a"}


def unhex(h: str) -> float | None:
    return None if set(h) <= {"."} else struct.unpack(">d", bytes.fromhex(h))[0]


for stem, gfile, tag in (
    ("x07_roc_ties", "x07_groups.json", "X07 roc "),
    ("x10_roc_stderr", "x10_groups.json", "X10 roc "),
    ("x10b_roc_stderr_boundary", "x10b_groups.json", "X10 roc "),
    ("x12_roc_one_obs", "x12_groups.json", "X12 roc "),
):
    text = re.sub(r"\n(?=(StdErr|LowerArea|UpperArea|SomersD|Gamma|TauA|Label2|nValue\d)=)", " ", (HERE / f"{stem}.log").read_text())
    roc = {int(m["g"]): m for m in (dict(re.findall(r"(\w+)=(\S+)", ln)) for ln in text.splitlines() if ln.startswith(tag))}
    groups = json.loads((HERE / gfile).read_text())
    exact, worst, cells = dict.fromkeys(COLS, 0), dict.fromkeys(COLS, 0.0), []
    for g in groups:
        rows = [(unhex(p) or 0.0, y) for p, y in g["rows"]]
        r = sas_compat.roc_association(pl.Series([float(y) for _, y in rows]), pl.Series([p for p, _ in rows], dtype=pl.Float64))
        for c, attr in COLS.items():
            port, sas = getattr(r, attr), unhex(roc[g["g"]][c])
            if sas_compat.sas_d8(port) != sas_compat.sas_d8(sas):
                cells.append((g["g"], c, sas_compat.sas_d8(sas), sas_compat.sas_d8(port)))
            if port == sas:
                exact[c] += 1
            elif port is None or sas is None:
                worst[c] = float("inf")
            else:
                worst[c] = max(worst[c], abs(port - sas))
    print(f"{stem}: {len(groups)} BY groups; printed cells that differ: {len(cells)} {cells[:10] if cells else ''}")
    for c in COLS:
        print(f"  {c:10s} bit-exact {exact[c]:3d}/{len(groups)}   largest difference {worst[c]:.3g}")
