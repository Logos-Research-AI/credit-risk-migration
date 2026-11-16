"""X16: sas_compat.classification_table on an intercept-only fit against SAS (x16_ctable_intercept_only.log).
Checks, for each of the 40 fits: SAS's cross-validated probability is the exact leave-one-out mean, bit for bit;
SAS's levels are the recurrence of the helper's docstring, bit for bit; the port's rows and four counts are SAS's.
Usage (from port/): uv run python ../migration/legacy-to-port/experiments/x16_port_check.py"""

import struct
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "port"))
from credit_risk import sas_compat  # noqa: E402


def h2f(h: str) -> float:
    return struct.unpack(">d", bytes.fromhex(h))[0]


ct: dict[tuple[int, int], list[tuple[float, int, int, int, int]]] = defaultdict(list)
xp: dict[tuple[int, int], dict[int, float]] = defaultdict(dict)
for line in (HERE / "x16_ctable_intercept_only.log").read_text().splitlines():
    if line.startswith("CT|"):
        _, n, e, rest = line.split("|")
        t = rest.split()
        ct[(int(n), int(e))].append((h2f(t[0]), int(t[2]), int(t[3]), int(t[4]), int(t[5])))
    elif line.startswith("XP|"):
        _, n, e, rest = line.split("|")
        t = rest.split()
        xp[(int(n), int(e))][int(t[0][2:])] = h2f(t[3].split("=")[1])

bad_xp = bad_levels = bad_tables = n_levels = 0
for (n, e), rows in ct.items():
    bad_xp += not (xp[(n, e)][1] == (e - 1) / (n - 1) and xp[(n, e)][0] == e / (n - 1))
    lv = [r[0] for r in rows]
    k0 = round(lv[0] / 0.02)
    mine = [k0 * 0.02]
    for i in range(1, len(lv)):
        mine.append(mine[i - 2] + 0.04 if i >= 2 and i % 2 == 0 else mine[i - 1] + 0.02)
    if k0 + len(lv) - 1 == 50:
        mine[-1] = 1.0 + 1e-12
    bad_levels += sum(a != b for a, b in zip(lv, mine, strict=True))
    n_levels += len(lv)
    y = np.array([1.0] * e + [0.0] * (n - e))
    tab = sas_compat.classification_table(y, np.ones((n, 1)), pd=np.full(n, e / n))
    port = [(f"{r[0]:.3f}", *r[1:5]) for r in tab.rows()]
    sas = [(f"{r[0]:.3f}", *r[1:]) for r in rows]
    if port != sas:
        bad_tables += 1
        print(f"n={n} events={e}: port differs from SAS", next((p, s) for p, s in zip(port, sas, strict=False) if p != s))
print(f"{len(ct)} fits, {n_levels} levels: {bad_xp} fits whose SAS probability is not the leave-one-out mean, "
      f"{bad_levels} levels not reproduced, {bad_tables} tables where the port differs from SAS")
